from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import QSettings

# Diccionario de colores con nombre → hex
COLOR_HEX = {
    "Azul": ("#4F81BD", "#3A6190"),
    "Verde": ("#2E8B57", "#206744"),
    "Naranja": ("#FFA500", "#CC8400"),
    "Rojo": ("#B22222", "#841818"),
    "Violeta": ("#800080", "#5A005A")
}



class ConfiguracionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración visual")
        layout = QVBoxLayout(self)

        # Tema
        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["Claro", "Oscuro", "Intermedio"])
        layout.addWidget(QLabel("Tema:"))
        layout.addWidget(self.combo_tema)

        # Color
        self.combo_color = QComboBox()
        self.combo_color.addItems(list(COLOR_HEX.keys()))
        layout.addWidget(QLabel("Color de acento:"))
        layout.addWidget(self.combo_color)

        # Fuente
        self.combo_fuente = QComboBox()
        self.combo_fuente.addItems(["10pt", "11pt", "12pt", "13pt", "14pt"])
        layout.addWidget(QLabel("Tamaño de fuente:"))
        layout.addWidget(self.combo_fuente)

        # Botones
        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")
        btn_guardar.clicked.connect(self._guardar_configuracion)
        btn_cancelar.clicked.connect(self.reject)
        h = QHBoxLayout()
        h.addWidget(btn_guardar)
        h.addWidget(btn_cancelar)
        layout.addLayout(h)

        self._cargar_configuracion()

    def _cargar_configuracion(self):
        settings = QSettings("MiInventario", "AppStock")
        tema = settings.value("tema", "Claro")
        color_hex = str(settings.value("color_acento", "#4F81BD"))
        fuente = str(settings.value("tam_fuente", "11pt"))

        self.combo_tema.setCurrentText(tema)

        # Buscar nombre de color
        nombre_color = next((k for k, v in COLOR_HEX.items() if v == color_hex), "Azul")
        self.combo_color.setCurrentText(nombre_color)

        self.combo_fuente.setCurrentText(fuente)

    def _guardar_configuracion(self):
        tema = self.combo_tema.currentText()
        color_nombre = self.combo_color.currentText()
        fuente = self.combo_fuente.currentText()

        color_hex, color_hover = COLOR_HEX[color_nombre]

        settings = QSettings("MiInventario", "AppStock")
        settings.setValue("tema", tema)
        settings.setValue("color_acento", color_hex)
        settings.setValue("color_acento_hover", color_hover)
        settings.setValue("tam_fuente", fuente)
        QMessageBox.information(self, "Guardado", "Configuración guardada correctamente.")
        self.accept()
