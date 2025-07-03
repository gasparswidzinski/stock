from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QCursor
from PySide6 import QtCore


class DashboardWidget(QWidget):
    def __init__(self, db, main_window, parent=None):
        super().__init__(parent)
        self.db = db
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # Resumen de stock
        self.label_total = QLabel()
        self.label_stock_bajo = QLabel()
        self.label_total_stock = QLabel()

        font = self.label_total.font()
        font.setPointSize(12)
        font.setBold(True)
        self.label_total.setFont(font)
        self.label_stock_bajo.setFont(font)
        self.label_total_stock.setFont(font)

        layout.addWidget(self.label_total)
        layout.addWidget(self.label_stock_bajo)
        layout.addWidget(self.label_total_stock)

        layout.addSpacing(20)

        # Botones de acción (6 botones rectangulares en 2 filas)
        grid = QGridLayout()
        grid.setSpacing(15)

        def crear_boton(icono, texto, callback):
            btn = QPushButton(f"  {texto}")
            btn.setIcon(QIcon(f"icons/{icono}"))
            btn.setIconSize(QSize(24, 24))
            btn.setMinimumHeight(50)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 10pt;
                    text-align: left;
                    padding: 8px 16px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
            """)
            btn.clicked.connect(callback)
            return btn

        # Botones (usa tus funciones de main_window)
        btn1 = crear_boton("add.png", "Nuevo Componente", self.main_window._on_agregar_componente)
        btn2 = crear_boton("folder.png", "Nuevo Proyecto", self.main_window._nuevo_proyecto)
        btn3 = crear_boton("inventory.png", "Ver Stock", self.main_window._mostrar_todo_stock)
        btn4 = crear_boton("import.png", "Importar Proyecto", self.main_window._importar_proyecto_csv)
        btn5 = crear_boton("folder.png", "Ver Proyectos", self.main_window._abrir_dialogo_proyectos)
        btn6 = crear_boton("tag.png", "Administrar Etiquetas", self.main_window._on_administrar_etiquetas)

        # Agregar al grid (2 filas x 3 columnas)
        grid.addWidget(btn1, 0, 0)
        grid.addWidget(btn2, 0, 1)
        grid.addWidget(btn3, 0, 2)
        grid.addWidget(btn4, 1, 0)
        grid.addWidget(btn5, 1, 1)
        grid.addWidget(btn6, 1, 2)

        layout.addLayout(grid)
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
        super().showEvent(event)
        self.setWindowOpacity(0.0)
        self.anim = QtCore.QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(300)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)
        self.anim.start()
