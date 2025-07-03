from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6 import QtCore



class DashboardWidget(QWidget):
    def __init__(self, db, main_window, parent=None):
        super().__init__(parent)
        self.db = db
        self.main_window = main_window

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        # Títulos grandes
        self.label_total = QLabel()
        self.label_stock_bajo = QLabel()
        self.label_total_stock = QLabel()

        font = self.label_total.font()
        font.setPointSize(12)
        font.setBold(True)
        self.label_total.setFont(font)
        self.label_stock_bajo.setFont(font)
        self.label_total_stock.setFont(font)

        # Resumen
        layout.addWidget(self.label_total)
        layout.addWidget(self.label_stock_bajo)
        layout.addWidget(self.label_total_stock)

        # Botones de acción rápida
        botones_layout = QHBoxLayout()

        btn_nuevo_componente = QPushButton(QIcon("icons/add.png"), "Nuevo Componente")
        btn_nuevo_componente.setIconSize(QtCore.QSize(24, 24))
        btn_nuevo_componente.clicked.connect(self.main_window._on_agregar_componente)

        btn_nuevo_proyecto = QPushButton(QIcon("icons/folder.png"), "Nuevo Proyecto")
        btn_nuevo_proyecto.setIconSize(QtCore.QSize(24, 24))
        btn_nuevo_proyecto.clicked.connect(self.main_window._nuevo_proyecto)

        btn_ver_stock = QPushButton(QIcon("icons/inventory.png"), "Ver Stock Completo")
        btn_ver_stock.setIconSize(QtCore.QSize(24, 24))
        btn_ver_stock.clicked.connect(self.main_window._mostrar_todo_stock)

        botones_layout.addWidget(btn_nuevo_componente)
        botones_layout.addWidget(btn_nuevo_proyecto)
        botones_layout.addWidget(btn_ver_stock)

        layout.addSpacing(20)
        layout.addLayout(botones_layout)

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

