from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class HistorialDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Historial de movimientos")
        self.resize(800, 500)

        layout = QVBoxLayout(self)

        titulo = QLabel("📜 Historial de movimientos")
        fuente = QFont()
        fuente.setPointSize(11)
        fuente.setBold(True)
        titulo.setFont(fuente)
        layout.addWidget(titulo)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha y Hora", "Acción", "Componente", "Cantidad", "Descripción"
        ])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabla)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_cerrar)
        layout.addLayout(h)

        self._cargar_datos()

    def _cargar_datos(self):
        c = self.db.conn.cursor()
        c.execute("""
        SELECT h.fecha_hora, h.accion, c.nombre, h.cantidad, h.descripcion
        FROM historial h
        LEFT JOIN componentes c ON h.componente_id = c.id
        ORDER BY h.fecha_hora DESC
        """)
        resultados = c.fetchall()

        self.tabla.setRowCount(0)
        for row_data in resultados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for col, value in enumerate(row_data):
                texto = str(value) if value is not None else "-"
                self.tabla.setItem(row, col, QTableWidgetItem(texto))
        self.tabla.resizeColumnsToContents()
