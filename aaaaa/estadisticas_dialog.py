from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QTabWidget, QWidget, QHBoxLayout
)
from PySide6.QtGui import QFont
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime, timedelta
from collections import defaultdict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFileDialog


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

       
        combo = QComboBox()
        combo.addItems(["Últimos 7 días", "Últimos 30 días", "Últimos 90 días"])
        layout.addWidget(combo)

        
        self.fig_evolucion = Figure(figsize=(8,4))
        self.ax_evolucion = self.fig_evolucion.add_subplot(111)

        
        self.fig_evolucion.patch.set_facecolor("#202124")
        self.ax_evolucion.set_facecolor("#202124")
        self.ax_evolucion.tick_params(colors="#e8eaed")
        self.ax_evolucion.xaxis.label.set_color("#e8eaed")
        self.ax_evolucion.yaxis.label.set_color("#e8eaed")
        self.ax_evolucion.title.set_color("#e8eaed")

        self.canvas_evolucion = FigureCanvas(self.fig_evolucion)
        layout.addWidget(self.canvas_evolucion)

        
        btn_guardar = QPushButton("Guardar imagen…")
        layout.addWidget(btn_guardar)

       
        def actualizar():
            texto = combo.currentText()
            dias = 7
            if "30" in texto:
                dias = 30
            elif "90" in texto:
                dias = 90
            self._actualizar_grafico_evolucion(dias)

        combo.currentIndexChanged.connect(actualizar)

       
        def guardar_imagen():
            ruta, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar imagen del gráfico",
                "evolucion_stock.png",
                "PNG (*.png);;PDF (*.pdf)"
            )
            if ruta:
                self.fig_evolucion.savefig(ruta, bbox_inches="tight")

        btn_guardar.clicked.connect(guardar_imagen)

        
        self._actualizar_grafico_evolucion(30)

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

    def _actualizar_grafico_evolucion(self, dias):

        hoy = datetime.now().date()
        fechas = [hoy - timedelta(days=i) for i in reversed(range(dias))]
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

        self.ax_evolucion.clear()
        self.ax_evolucion.set_facecolor("#202124")
        self.ax_evolucion.plot(fecha_labels, valores, marker="o", color="#4F81BD")
        self.ax_evolucion.set_title(f"Evolución del stock en los últimos {dias} días")
        self.ax_evolucion.set_xlabel("Fecha")
        self.ax_evolucion.set_ylabel("Stock total acumulado")
        if dias > 30:
            paso = dias // 10 
            indices = list(range(0, dias, paso))
            etiquetas_reducidas = [fecha_labels[i] for i in indices]
            self.ax_evolucion.set_xticks(indices)
            self.ax_evolucion.set_xticklabels(etiquetas_reducidas, rotation=45)
        else:
            self.ax_evolucion.set_xticks(range(len(fecha_labels)))
            self.ax_evolucion.set_xticklabels(fecha_labels, rotation=45)
        self.ax_evolucion.grid(True)
        self.fig_evolucion.autofmt_xdate(rotation=45)
        self.fig_evolucion.tight_layout()
        self.canvas_evolucion.draw()
        self.canvas_evolucion.draw()
