from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from dialogs import ItemDialog

class ProyectoWidget(QWidget):
    def __init__(self, db, main_window, tipo="prototipo", proyecto_id=None):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.tipo = tipo
        self.proyecto_id = proyecto_id
        self.componentes = []  # lista de dicts con id y cantidad

        self.setFocusPolicy(Qt.StrongFocus)

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Cantidad", "Stock disponible"])
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        layout.addWidget(self.table)

        botones = QHBoxLayout()
        btn_agregar = QPushButton("Agregar componente")
        btn_agregar.clicked.connect(self._agregar_componente)
        btn_quitar = QPushButton("Quitar seleccionado")
        btn_quitar.clicked.connect(self._quitar_seleccionado)
        btn_guardar = QPushButton("Guardar prototipo")
        btn_guardar.clicked.connect(self._guardar_prototipo)
        btn_soldar = QPushButton("Soldar")
        btn_soldar.clicked.connect(self._soldar_proyecto)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self._cerrar)

        botones.addWidget(btn_agregar)
        botones.addWidget(btn_quitar)
        botones.addWidget(btn_guardar)
        botones.addWidget(btn_soldar)
        botones.addWidget(btn_cerrar)
        layout.addLayout(botones)

        self.table.itemChanged.connect(self._on_cantidad_editada)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Insert:
            self._agregar_componente()
        else:
            super().keyPressEvent(event)

    def _agregar_componente(self):
        dlg = ItemDialog(self.db, self)
        dlg.componente_guardado.connect(self._on_componente_guardado)
        dlg.exec()

    def _quitar_seleccionado(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        comp_id = int(self.table.item(row, 0).text())
        self.componentes = [c for c in self.componentes if c["id"] != comp_id]
        self._actualizar_tabla()

    def _on_cantidad_editada(self, item):
        if item.column() != 2:
            return
        try:
            nueva_cantidad = int(item.text())
            if nueva_cantidad <= 0:
                QMessageBox.warning(self, "Cantidad inválida", "La cantidad debe ser mayor que cero.")
                self._actualizar_tabla()
                return
            comp_id = int(self.table.item(item.row(), 0).text())
            for c in self.componentes:
                if c["id"] == comp_id:
                    c["cantidad"] = nueva_cantidad
                    break
            self._actualizar_tabla()
        except ValueError:
            QMessageBox.warning(self, "Error", "La cantidad debe ser un número entero.")
            self._actualizar_tabla()

    def _actualizar_tabla(self):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for c in self.componentes:
            info = self.db.obtener_componente_por_id(c["id"])
            stock_disp = info["cantidad"]
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_item = QTableWidgetItem(str(c["id"]))
            nombre_item = QTableWidgetItem(info["nombre"])
            cantidad_item = QTableWidgetItem(str(c["cantidad"]))
            cantidad_item.setTextAlignment(Qt.AlignCenter)
            stock_item = QTableWidgetItem(str(stock_disp))
            stock_item.setTextAlignment(Qt.AlignCenter)

            # Resaltar en rojo si solicitado > stock
            if c["cantidad"] > stock_disp:
                cantidad_item.setBackground(Qt.red)
                cantidad_item.setForeground(Qt.white)

            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, nombre_item)
            self.table.setItem(row, 2, cantidad_item)
            self.table.setItem(row, 3, stock_item)

        self.table.resizeColumnsToContents()
        self.table.blockSignals(False)

    def _guardar_prototipo(self):
        if not self._validar_cantidades():
            return
        nombre, ok = self.main_window._dialogo_nombre_proyecto("Guardar prototipo")
        if not ok or not nombre.strip():
            return
        self.db.guardar_proyecto(nombre.strip(), "prototipo", self.componentes)
        QMessageBox.information(self, "Guardado", "Prototipo guardado exitosamente.")

    def _soldar_proyecto(self):
        if not self._validar_cantidades():
            return
        # Chequear si hay faltantes
        faltantes = []
        for c in self.componentes:
            info = self.db.obtener_componente_por_id(c["id"])
            if c["cantidad"] > info["cantidad"]:
                faltantes.append(info["nombre"])
        if faltantes:
            QMessageBox.warning(
                self,
                "Error de stock",
                f"No hay stock suficiente para: {', '.join(faltantes)}"
            )
            return

        nombre, ok = self.main_window._dialogo_nombre_proyecto("Soldar proyecto")
        if not ok or not nombre.strip():
            return
        exito, _ = self.db.soldar_proyecto(nombre.strip(), self.componentes)
        QMessageBox.information(self, "Soldado", "Proyecto soldado y stock actualizado.")

    def _on_componente_guardado(self, comp_id):
        existente = next((c for c in self.componentes if c["id"] == comp_id), None)
        if existente:
            existente["cantidad"] += 1
        else:
            self.componentes.append({"id": comp_id, "cantidad": 1})
        self._actualizar_tabla()

    def _validar_cantidades(self):
        for c in self.componentes:
            if c["cantidad"] <= 0:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Hay componentes con cantidad inválida (<=0). Corrige antes de continuar."
                )
                return False
        return True

    def _cerrar(self):
        # Restaurar la ventana principal
        self.main_window.setCentralWidget(None)
