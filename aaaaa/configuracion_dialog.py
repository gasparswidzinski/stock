from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QHBoxLayout
)
from PySide6.QtCore import Qt, QSettings


class ConfiguracionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configuración de Apariencia")
        self.resize(400, 250)

        layout = QVBoxLayout(self)

        # Tema
        h_tema = QHBoxLayout()
        h_tema.addWidget(QLabel("Tema:"))
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["Claro", "Oscuro", "Intermedio"])
        h_tema.addWidget(self.combo_tema)
        layout.addLayout(h_tema)

        # Color acento
        h_color = QHBoxLayout()
        h_color.addWidget(QLabel("Color de acento:"))
        self.combo_color = QComboBox()
        self.combo_color.addItems(["Azul", "Verde", "Naranja", "Rojo", "Violeta"])
        h_color.addWidget(self.combo_color)
        layout.addLayout(h_color)

        # Tamaño de fuente
        h_fuente = QHBoxLayout()
        h_fuente.addWidget(QLabel("Tamaño de fuente:"))
        self.spin_fuente = QSpinBox()
        self.spin_fuente.setRange(8, 20)
        h_fuente.addWidget(self.spin_fuente)
        layout.addLayout(h_fuente)

        # Botones
        btn_aplicar = QPushButton("Aplicar")
        btn_aplicar.clicked.connect(self._aplicar)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.accept)

        h_btn = QHBoxLayout()
        h_btn.addWidget(btn_aplicar)
        h_btn.addStretch()
        h_btn.addWidget(btn_cerrar)
        layout.addLayout(h_btn)

        # Cargar preferencias
        self._cargar_preferencias()

    def _cargar_preferencias(self):
        settings = QSettings("MiInventario", "AppStock")
        tema = settings.value("tema", "Claro")
        color = settings.value("color_acento", "Azul")
        fuente = int(settings.value("tam_fuente", 10))

        self.combo_tema.setCurrentText(tema)
        self.combo_color.setCurrentText(color)
        self.spin_fuente.setValue(fuente)

    def _aplicar(self):
        tema = self.combo_tema.currentText()
        color = self.combo_color.currentText()
        tam_fuente = self.spin_fuente.value()

        settings = QSettings("MiInventario", "AppStock")
        settings.setValue("tema", tema)
        settings.setValue("color_acento", color)
        settings.setValue("tam_fuente", tam_fuente)

        # Aplicar inmediatamente
        self.parent()._aplicar_configuracion_visual()
