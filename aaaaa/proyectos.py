from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from dialogs import ItemDialog
from PySide6.QtGui import QIcon
from PySide6 import QtCore


class ProyectoWidget(QWidget):
    def __init__(self, db, main_window, tipo="prototipo", proyecto_id=None):
        super().__init__()
        self.db = db
        self.main_window = main_window
        self.tipo = tipo
        self.proyecto_id = proyecto_id

        self.setFocusPolicy(Qt.StrongFocus)

        
        self.componentes = []
        todos = self.db.obtener_componentes_todos()
        for comp in todos:
            self.componentes.append({"id": comp["id"], "cantidad": 0})

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre", "Cantidad", "Stock disponible"])
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)
        layout.addWidget(self.table)

        botones = QHBoxLayout()
        btn_guardar = QPushButton(QIcon("icons/save.png"), "Guardar prototipo")
        btn_guardar.setIconSize(QtCore.QSize(24, 24))
        btn_guardar.clicked.connect(self._guardar_prototipo)
        btn_soldar = QPushButton(QIcon("icons/folder.png"), "Soldar")
        btn_soldar.setIconSize(QtCore.QSize(24, 24))
        btn_soldar.clicked.connect(self._soldar_proyecto)
        btn_cerrar = QPushButton(QIcon("icons/cancel.png"), "Cerrar")
        btn_cerrar.setIconSize(QtCore.QSize(24, 24))
        btn_cerrar.clicked.connect(self._cerrar)

        botones.addWidget(btn_guardar)
        botones.addWidget(btn_soldar)
        botones.addStretch()
        botones.addWidget(btn_cerrar)
        layout.addLayout(botones)

        self.table.itemChanged.connect(self._on_cantidad_editada)

        self._actualizar_tabla()
        

    def keyPressEvent(self, event):
        super().keyPressEvent(event)

    def _on_cantidad_editada(self, item):
        if item.column() != 2:
            return
        try:
            nueva_cantidad = int(item.text())
            if nueva_cantidad < 0:
                QMessageBox.warning(self, "Cantidad inválida", "La cantidad no puede ser negativa.")
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
        componentes_a_guardar = [c for c in self.componentes if c["cantidad"] > 0]
        self.db.guardar_proyecto(nombre.strip(), "prototipo", componentes_a_guardar)
        QMessageBox.information(self, "Guardado", "Prototipo guardado exitosamente.")
        self.main_window._mostrar_dashboard()

    def _soldar_proyecto(self):
        if not self._validar_cantidades():
            return
        componentes_a_soldar = [c for c in self.componentes if c["cantidad"] > 0]
        faltantes = []
        for c in componentes_a_soldar:
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
        exito, _ = self.db.soldar_proyecto(nombre.strip(), componentes_a_soldar)
        QMessageBox.information(self, "Soldado", "Proyecto soldado y stock actualizado.")
        self.main_window._mostrar_dashboard()

    def _validar_cantidades(self):
        for c in self.componentes:
            if c["cantidad"] < 0:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Hay componentes con cantidad inválida (menor que cero)."
                )
                return False
        return True

    def _cerrar(self):
        self.main_window._mostrar_dashboard()
