from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

class HistorialDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Historial de movimientos")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        titulo = QLabel("📜 Historial de movimientos")
        fuente = QFont()
        fuente.setPointSize(11)
        fuente.setBold(True)
        titulo.setFont(fuente)
        layout.addWidget(titulo)

        # Filtros
        filtros_layout = QHBoxLayout()

        self.texto_busqueda = QLineEdit()
        self.texto_busqueda.setPlaceholderText("Buscar texto...")

        self.combo_accion = QComboBox()
        self.combo_accion.addItem("Todas las acciones")
        self.combo_accion.addItems(["Alta", "Edición", "Baja", "Entrada Stock"])

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDisplayFormat("yyyy-MM-dd")
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-1))

        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDisplayFormat("yyyy-MM-dd")
        self.fecha_hasta.setDate(QDate.currentDate())

        btn_aplicar = QPushButton("Aplicar filtros")
        btn_aplicar.clicked.connect(self._cargar_datos)

        filtros_layout.addWidget(QLabel("Buscar:"))
        filtros_layout.addWidget(self.texto_busqueda)
        filtros_layout.addWidget(QLabel("Acción:"))
        filtros_layout.addWidget(self.combo_accion)
        filtros_layout.addWidget(QLabel("Desde:"))
        filtros_layout.addWidget(self.fecha_desde)
        filtros_layout.addWidget(QLabel("Hasta:"))
        filtros_layout.addWidget(self.fecha_hasta)
        filtros_layout.addWidget(btn_aplicar)

        layout.addLayout(filtros_layout)

        # Tabla de resultados
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha y Hora", "Acción", "Componente", "Cantidad", "Descripción"
        ])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.tabla)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_cerrar)
        layout.addLayout(h)

        # Cargar datos iniciales
        self._cargar_datos()

    def _cargar_datos(self):
        texto = self.texto_busqueda.text().strip().lower()
        accion = self.combo_accion.currentText()
        fecha_desde = self.fecha_desde.date().toString("yyyy-MM-dd")
        fecha_hasta = self.fecha_hasta.date().toString("yyyy-MM-dd")

        query = """
        SELECT h.fecha_hora, h.accion, c.nombre, h.cantidad, h.descripcion
        FROM historial h
        LEFT JOIN componentes c ON h.componente_id = c.id
        WHERE date(h.fecha_hora) BETWEEN ? AND ?
        """
        params = [fecha_desde, fecha_hasta]

        if accion != "Todas las acciones":
            query += " AND h.accion = ?"
            params.append(accion)

        c = self.db.conn.cursor()
        c.execute(query, params)
        resultados = c.fetchall()

        # Filtrar por texto en Python
        if texto:
            resultados = [
                r for r in resultados
                if any(texto in (str(value).lower() if value else "") for value in r)
            ]

        self.tabla.setRowCount(0)
        for row_data in resultados:
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)
            for col, value in enumerate(row_data):
                texto_item = str(value) if value is not None else "-"
                self.tabla.setItem(row, col, QTableWidgetItem(texto_item))

        self.tabla.resizeColumnsToContents()
