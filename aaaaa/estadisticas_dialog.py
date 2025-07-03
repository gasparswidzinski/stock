from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTabWidget, QWidget, QHBoxLayout
)
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from collections import defaultdict
from PySide6.QtCore import Qt


class EstadisticasDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("📊 Estadísticas de Inventario")
        self.resize(900, 700)

        layout = QVBoxLayout(self)

        titulo = QLabel("📊 Estadísticas de Inventario")
        fuente = QFont()
        fuente.setPointSize(11)
        fuente.setBold(True)
        titulo.setFont(fuente)
        layout.addWidget(titulo)

        tabs = QTabWidget()
        tabs.addTab(self._tab_evolucion(), "Evolución de Stock")
        tabs.addTab(self._tab_ranking(), "Ranking de Movimientos")
        tabs.addTab(self._tab_resumen(), "Resumen General")

        layout.addWidget(tabs)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(btn_cerrar)
        layout.addLayout(h)

    def _tab_evolucion(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        fig = Figure(figsize=(8,4))
        ax = fig.add_subplot(111)

        # Configurar colores para tema oscuro
        fig.patch.set_facecolor("#202124")
        ax.set_facecolor("#202124")
        ax.tick_params(colors="#e8eaed")
        ax.xaxis.label.set_color("#e8eaed")
        ax.yaxis.label.set_color("#e8eaed")
        ax.title.set_color("#e8eaed")

        # Últimos 30 días
        hoy = datetime.now().date()
        fechas = [hoy - timedelta(days=i) for i in reversed(range(30))]
        fecha_labels = [f.strftime("%d-%m") for f in fechas]
        stock_por_dia = defaultdict(int)

        c = self.db.conn.cursor()
        c.execute("""
            SELECT fecha_hora, accion, cantidad
            FROM historial
            ORDER BY fecha_hora ASC
        """)
        filas = c.fetchall()

        acumulado = 0
        movimientos = []
        for r in filas:
            fecha = datetime.fromisoformat(r["fecha_hora"]).date()
            cantidad = r["cantidad"] or 0
            if r["accion"] == "Alta":
                acumulado += cantidad
            elif r["accion"] == "Baja":
                acumulado -= cantidad
            movimientos.append((fecha, acumulado))

        ult_valor = 0
        for f in fechas:
            dias_previos = [v for v in movimientos if v[0] <= f]
            if dias_previos:
                ult_valor = dias_previos[-1][1]
            stock_por_dia[f] = max(ult_valor, 0)

        valores = [stock_por_dia[f] for f in fechas]
        ax.plot(fecha_labels, valores, marker="o", color="#4F81BD")
        ax.set_title("Evolución del stock en los últimos 30 días")
        ax.set_xlabel("Fecha")
        ax.set_ylabel("Stock total acumulado")
        ax.grid(True)

        fig.autofmt_xdate()
        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        return widget

    def _tab_ranking(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        fig = Figure(figsize=(8,4))
        ax = fig.add_subplot(111)

        # Configurar colores para tema oscuro
        fig.patch.set_facecolor("#202124")
        ax.set_facecolor("#202124")
        ax.tick_params(colors="#e8eaed")
        ax.xaxis.label.set_color("#e8eaed")
        ax.yaxis.label.set_color("#e8eaed")
        ax.title.set_color("#e8eaed")

        c = self.db.conn.cursor()
        c.execute("""
            SELECT c.nombre, COUNT(*) as total
            FROM historial h
            LEFT JOIN componentes c ON h.componente_id = c.id
            GROUP BY c.nombre
            ORDER BY total DESC
            LIMIT 10
        """)
        data = c.fetchall()

        if not data:
            label = QLabel("No hay datos de movimientos.")
            layout.addWidget(label)
            return widget

        nombres = [r["nombre"] or "(Desconocido)" for r in data]
        totales = [r["total"] for r in data]

        ax.barh(nombres[::-1], totales[::-1], color="#9BBB59")
        ax.set_xlabel("Cantidad de movimientos")
        ax.set_title("Top 10 componentes con más movimientos")

        canvas = FigureCanvas(fig)
        layout.addWidget(canvas)
        return widget

    def _tab_resumen(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        c = self.db.conn.cursor()
        c.execute("SELECT COUNT(*) FROM componentes")
        total_componentes = c.fetchone()[0]

        c.execute("SELECT SUM(cantidad) FROM componentes")
        total_stock = c.fetchone()[0] or 0

        c.execute("SELECT MAX(fecha_hora) FROM historial")
        ultima_fecha = c.fetchone()[0] or "-"

        resumen = f"""
<div style="color:#e8eaed;">
<b>Total de componentes distintos:</b> {total_componentes}<br>
<b>Stock total actual:</b> {total_stock}<br>
<b>Última modificación:</b> {ultima_fecha}
</div>
"""
        lbl = QLabel(resumen)
        lbl.setTextFormat(Qt.TextFormat.RichText)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(lbl)
        return widget
