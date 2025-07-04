from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QComboBox, QLabel,
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import QSettings

class ConfiguracionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración Visual")
        layout = QVBoxLayout(self)

        self.combo_tema = QComboBox()
        self.combo_tema.addItems(["Claro", "Oscuro", "Intermedio"])
        layout.addWidget(QLabel("Tema:"))
        layout.addWidget(self.combo_tema)

        self.combo_color = QComboBox()
        self.combo_color.addItems(["Azul", "Verde", "Naranja", "Rojo", "Violeta"])
        layout.addWidget(QLabel("Color de acento:"))
        layout.addWidget(self.combo_color)

        self.combo_fuente = QComboBox()
        self.combo_fuente.addItems(["10pt", "11pt", "12pt", "13pt"])
        layout.addWidget(QLabel("Tamaño de fuente:"))
        layout.addWidget(self.combo_fuente)

        botones = QHBoxLayout()
        btn_guardar = QPushButton("Guardar")
        btn_cancelar = QPushButton("Cancelar")
        botones.addWidget(btn_guardar)
        botones.addWidget(btn_cancelar)
        layout.addLayout(botones)

        btn_guardar.clicked.connect(self.guardar)
        btn_cancelar.clicked.connect(self.reject)

        self._cargar_configuracion()

    def _cargar_configuracion(self):
        settings = QSettings("MiInventario", "AppStock")
        tema = settings.value("tema", "Claro")
        color = settings.value("color_acento", "Azul")
        fuente = settings.value("tam_fuente", "11pt")

        self.combo_tema.setCurrentText(tema)
        self.combo_color.setCurrentText(color)
        self.combo_fuente.setCurrentText(fuente)

    def guardar(self):
        settings = QSettings("MiInventario", "AppStock")
        settings.setValue("tema", self.combo_tema.currentText())
        settings.setValue("color_acento", self.combo_color.currentText())
        settings.setValue("tam_fuente", self.combo_fuente.currentText())
        QMessageBox.information(self, "Configuración", "Los cambios se aplicarán al reiniciar la aplicación.")
        self.accept()
