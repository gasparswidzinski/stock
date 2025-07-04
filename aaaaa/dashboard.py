from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGridLayout
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from utils import fade_in

class DashboardWidget(QWidget):
    def __init__(self, db, main_window):
        super().__init__()
        self.db = db
        self.main_window = main_window

        layout = QVBoxLayout(self)

        # Labels separados
        self.label_total = QLabel()
        self.label_stock_bajo = QLabel()
        self.label_total_stock = QLabel()
        for lbl in (self.label_total, self.label_stock_bajo, self.label_total_stock):
            lbl.setAlignment(Qt.AlignLeft)
            lbl.setStyleSheet("font-size: 11pt;")
            layout.addWidget(lbl)

        grid = QGridLayout()
        layout.addLayout(grid)

        def crear_boton(icono, texto, callback):
            btn = QPushButton(QIcon(f"icons/{icono}"), f"  {texto}")
            btn.setMinimumHeight(50)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 10.5pt;
                    text-align: left;
                    padding: 8px;
                }
                QPushButton:hover {
                    border: 1px solid #888;
                }
            """)
            btn.clicked.connect(callback)
            return btn

        btn_nuevo = crear_boton("add.png", "Nuevo Componente", self.main_window._on_agregar_componente)
        btn_proyecto = crear_boton("folder.png", "Nuevo Proyecto", self.main_window._nuevo_proyecto)
        btn_stock = crear_boton("inventory.png", "Ver Todo el Stock", self.main_window._mostrar_todo_stock)
        btn_importar = crear_boton("import.png", "Importar Proyecto CSV", self.main_window._importar_proyecto_csv)
        btn_proyectos = crear_boton("folder.png", "Ver Proyectos Guardados", self.main_window._abrir_dialogo_proyectos)
        btn_etiquetas = crear_boton("tag.png", "Administrar Etiquetas", self.main_window._on_administrar_etiquetas)

        grid.addWidget(btn_nuevo, 0, 0)
        grid.addWidget(btn_proyecto, 0, 1)
        grid.addWidget(btn_stock, 1, 0)
        grid.addWidget(btn_importar, 1, 1)
        grid.addWidget(btn_proyectos, 2, 0)
        grid.addWidget(btn_etiquetas, 2, 1)

        grid.setVerticalSpacing(12)
        grid.setHorizontalSpacing(12)

        self._actualizar_datos()

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

    def showEvent(self, event):
        self._actualizar_datos()
        fade_in(self)
        super().showEvent(event)
