from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Cantidad"])
        layout.addWidget(self.table)

        botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar prototipo")
        btn_guardar.clicked.connect(self._guardar_prototipo)
        btn_soldar = QPushButton("Soldar")
        btn_soldar.clicked.connect(self._soldar_proyecto)
        botones.addWidget(btn_guardar)
        botones.addWidget(btn_soldar)
        layout.addLayout(botones)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Insert:
            self._agregar_componente()
        else:
            super().keyPressEvent(event)

    def _agregar_componente(self):
        dlg = ItemDialog(self.db, self)
        if dlg.exec():
            comp_id = dlg.comp_id if hasattr(dlg, "comp_id") else dlg.result()
            if not comp_id:
                return
            existente = next((c for c in self.componentes if c["id"] == comp_id), None)
            if existente:
                existente["cantidad"] += 1
            else:
                self.componentes.append({"id": comp_id, "cantidad": 1})
            self._actualizar_tabla()

    def _actualizar_tabla(self):
        self.table.setRowCount(0)
        for c in self.componentes:
            info = self.db.obtener_componente_por_id(c["id"])
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(c["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(info["nombre"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(c["cantidad"])))
        self.table.resizeColumnsToContents()

    def _guardar_prototipo(self):
        nombre, ok = self.main_window._dialogo_nombre_proyecto("Guardar prototipo")
        if not ok or not nombre.strip():
            return
        self.db.guardar_proyecto(nombre.strip(), "prototipo", self.componentes)
        QMessageBox.information(self, "Guardado", "Prototipo guardado exitosamente.")

    def _soldar_proyecto(self):
        nombre, ok = self.main_window._dialogo_nombre_proyecto("Soldar proyecto")
        if not ok or not nombre.strip():
            return
        exito, faltantes = self.db.soldar_proyecto(nombre.strip(), self.componentes)
        if not exito:
            QMessageBox.warning(self, "Error", f"No hay stock suficiente para: {', '.join(faltantes)}")
            return
        QMessageBox.information(self, "Soldado", "Proyecto soldado y stock actualizado.")
