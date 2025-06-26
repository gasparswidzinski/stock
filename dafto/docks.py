from PySide6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
)
from PySide6.QtCore import Slot
from dialogs import ItemDialog

class TagDockWidget(QDockWidget):
    def __init__(self, etiqueta, db, parent=None):
        super().__init__(etiqueta, parent)
        self.etiqueta = etiqueta
        self.db = db
        self.setObjectName(f"Dock_{etiqueta}")
        self.widget = QWidget()
        self.setWidget(self.widget)
        v = QVBoxLayout(self.widget)

        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Filtro:"))
        self.edit_filtro = QLineEdit()
        self.edit_filtro.textChanged.connect(self._on_filtrar)
        filtro_layout.addWidget(self.edit_filtro)
        v.addLayout(filtro_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Cantidad", "Ubicación"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        v.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_editar = QPushButton("Editar")
        btn_editar.clicked.connect(self._editar_seleccionado)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(self._eliminar_seleccionado)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_eliminar)
        v.addLayout(btn_layout)

        self._cargar_items()

    def _cargar_items(self):
        items = self.db.obtener_componentes_por_etiqueta(self.etiqueta)
        self._full_items = items
        self._mostrar_items(items)

    def _mostrar_items(self, items):
        self.table.setRowCount(0)
        for row_data in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(row_data["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(row_data["nombre"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data["cantidad"])))
            self.table.setItem(row, 3, QTableWidgetItem(row_data.get("ubicacion", "") or ""))
        self.table.resizeColumnsToContents()

    @Slot()
    def actualizar_lista(self):
        self._cargar_items()

    @Slot(str)
    def _on_filtrar(self, texto):
        texto = texto.lower()
        filtrados = []
        for item in self._full_items:
            if texto in item["nombre"].lower() or texto in (item.get("ubicacion", "") or "").lower():
                filtrados.append(item)
        self._mostrar_items(filtrados)

    @Slot()
    def _editar_seleccionado(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        comp_id = int(self.table.item(row, 0).text())
        dlg = ItemDialog(self.db, parent=self, comp_id=comp_id)
        dlg.componente_guardado.connect(self._on_item_guardado_externo)
        if dlg.exec():
            self.actualizar_lista()
            self.parent().on_componente_guardado(comp_id)

    @Slot()
    def _eliminar_seleccionado(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        comp_id = int(self.table.item(row, 0).text())
        resp = QMessageBox.question(self, "Confirmar", f"¿Eliminar componente ID {comp_id}?")
        if resp == QMessageBox.Yes:
            self.db.eliminar_componente(comp_id)
            self.actualizar_lista()
            self.parent().on_componente_eliminado(comp_id)

    @Slot(int)
    def _on_item_guardado_externo(self, comp_id):
        self.actualizar_lista()
