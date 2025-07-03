import sys
from PySide6.QtWidgets import QApplication
from mainwindow import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    
    with open("estilo.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    from datetime import datetime

    hora_actual = datetime.now().hour

    if 7 <= hora_actual < 19:
        tema = "tema_claro.qss"
    else:
        tema = "tema_oscuro.qss"

    window._cargar_tema(tema)
    window.show()
    sys.exit(app.exec())