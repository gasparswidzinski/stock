import csv
import os
from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from openpyxl import Workbook

def fade_in(widget):
    """Animación de opacidad."""
    from PySide6.QtCore import QPropertyAnimation
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(250)
    anim.setStartValue(0)
    anim.setEndValue(1)
    anim.start()
    widget._animation = anim

def exportar_csv(ruta, headers, filas):
    """Exporta una lista de filas a CSV."""
    try:
        with open(ruta, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(filas)
    except Exception as e:
        raise Exception(f"Error al exportar CSV:\n{e}")

def exportar_excel(ruta, headers, filas):
    """Exporta una lista de filas a Excel."""
    try:
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in filas:
            ws.append(row)
        wb.save(ruta)
    except Exception as e:
        raise Exception(f"Error al exportar Excel:\n{e}")

def cargar_tema(window, nombre_archivo, accent_color, font_size):
    """Carga QSS reemplazando placeholders dinámicos."""
    ruta = os.path.join(os.path.dirname(__file__), nombre_archivo)
    if not os.path.exists(ruta):
        return
    with open(ruta, "r", encoding="utf-8") as f:
        contenido = f.read()
    contenido = contenido.replace("{accent_color}", accent_color).replace("{font_size}", font_size)
    window.setStyleSheet(contenido)
