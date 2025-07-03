from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class EstadisticasDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Estadísticas de Inventario")
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        titulo = QLabel("📊 Estadísticas de Inventario")
        fuente = QFont()
        fuente.setPointSize(11)
        fuente.setBold(True)
        titulo.setFont(fuente)
        layout.addWidget(titulo)

        # Gráfico de barras: stock total por etiqueta
        self._grafico_barras(layout)

        # Gráfico de pastel: acciones en historial
        self._grafico_pastel(layout)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_cerrar)
        layout.addLayout(h)

    def _grafico_barras(self, layout):
        c = self.db.conn.cursor()
        c.execute("""
            SELECT e.nombre, SUM(c.cantidad) as total
            FROM componentes c
            JOIN componentes_etiquetas ce ON c.id = ce.componente_id
            JOIN etiquetas e ON ce.etiqueta_id = e.id
            GROUP BY e.nombre
            ORDER BY e.nombre COLLATE NOCASE
        """)
        data = c.fetchall()

        if not data:
            label = QLabel("No hay datos de stock por etiqueta.")
            layout.addWidget(label)
            return

        etiquetas = [r[0] for r in data]
        cantidades = [r[1] for r in data]

        fig = Figure(figsize=(6,3))
        ax = fig.add_subplot(111)
        ax.barh(etiquetas, cantidades, color="#5c9bd1")
        ax.set_xlabel("Cantidad total")
        ax.set_title("Stock total por etiqueta")

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)

    def _grafico_pastel(self, layout):
        c = self.db.conn.cursor()
        c.execute("""
            SELECT accion, COUNT(*) as total
            FROM historial
            GROUP BY accion
        """)
        data = c.fetchall()

        if not data:
            label = QLabel("No hay datos de movimientos en historial.")
            layout.addWidget(label)
            return

        acciones = [r[0] for r in data]
        cantidades = [r[1] for r in data]

        fig = Figure(figsize=(4,4))
        ax = fig.add_subplot(111)
        ax.pie(cantidades, labels=acciones, autopct="%1.1f%%", startangle=90)
        ax.set_title("Distribución de acciones en historial")

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
