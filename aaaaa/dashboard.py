from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QGroupBox
)
from PySide6.QtCore import Qt


class DashboardWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        
        self.label_total = QLabel()
        self.label_stock_bajo = QLabel()
        self.label_total_stock = QLabel()
        layout.addWidget(self._grupo_estadisticas())

       
        layout.addWidget(self._tabla_proyectos())

        self._actualizar_datos()

    def _grupo_estadisticas(self):
        box = QGroupBox("Resumen de Inventario")
        inner = QVBoxLayout(box)
        inner.addWidget(self.label_total)
        inner.addWidget(self.label_stock_bajo)
        inner.addWidget(self.label_total_stock)
        return box

    def _tabla_proyectos(self):
        box = QGroupBox("Últimos proyectos")
        inner = QVBoxLayout(box)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Nombre", "Fecha", "Tipo"])
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.MultiSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionMode(QTableWidget.NoSelection)
        self.tabla.setFocusPolicy(Qt.NoFocus)
        self.tabla.setFixedHeight(180)

        inner.addWidget(self.tabla)
        return box

    def _actualizar_datos(self):
        c = self.db.conn.cursor()

        c.execute("SELECT COUNT(*) FROM componentes")
        total = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM componentes WHERE stock_minimo IS NOT NULL AND cantidad < stock_minimo")
        bajos = c.fetchone()[0]

        c.execute("SELECT SUM(cantidad) FROM componentes")
        total_stock = c.fetchone()[0] or 0

        self.label_total.setText(f"🧮 Total de componentes: {total}")
        self.label_stock_bajo.setText(f"🔴 Con stock bajo: {bajos}")
        self.label_total_stock.setText(f"📦 Unidades totales en stock: {total_stock}")

        c.execute("SELECT nombre, fecha, tipo FROM proyectos ORDER BY fecha DESC LIMIT 5")
        proyectos = c.fetchall()
        self.tabla.setRowCount(0)
        for r in proyectos:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            self.tabla.setItem(row, 0, QTableWidgetItem(r["nombre"]))
            self.tabla.setItem(row, 1, QTableWidgetItem(r["fecha"]))
            self.tabla.setItem(row, 2, QTableWidgetItem(r["tipo"].capitalize()))
        self.tabla.resizeColumnsToContents()
