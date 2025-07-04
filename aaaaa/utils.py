from PySide6.QtWidgets import QFileDialog, QMessageBox
import csv
import openpyxl
from PySide6.QtCore import QPropertyAnimation


def cargar_tema(window, archivo_qss, color_acento="#4F81BD", tam_fuente="11pt"):
    import os

    ruta = os.path.join(os.path.dirname(__file__), archivo_qss)

    if not os.path.exists(ruta):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(window, "Error", f"No se encontró el archivo de tema:\n{ruta}")
        return

    with open(ruta, "r", encoding="utf-8") as f:
        estilo = f.read()

    estilo = (
        estilo
        .replace("$COLOR_ACCENT", color_acento)
        .replace("$FONT_SIZE", tam_fuente)
    )

    window.setStyleSheet(estilo)



def exportar_csv(parent, encabezados, datos, titulo="Exportar CSV"):
    """
    Exporta una lista de datos a CSV.
    """
    ruta, _ = QFileDialog.getSaveFileName(
        parent,
        titulo,
        "",
        "Archivos CSV (*.csv)"
    )
    if not ruta:
        return

    try:
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(encabezados)
            writer.writerows(datos)

        QMessageBox.information(parent, "Exportación exitosa", f"Archivo guardado en:\n{ruta}")
    except Exception as e:
        QMessageBox.critical(parent, "Error al exportar", str(e))


def exportar_excel(parent, encabezados, datos, titulo="Exportar Excel"):
    """
    Exporta una lista de datos a Excel (.xlsx).
    """
    ruta, _ = QFileDialog.getSaveFileName(
        parent,
        titulo,
        "",
        "Archivos Excel (*.xlsx)"
    )
    if not ruta:
        return

    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(encabezados)
        for fila in datos:
            ws.append(fila)
        wb.save(ruta)
        QMessageBox.information(parent, "Exportación exitosa", f"Archivo guardado en:\n{ruta}")
    except Exception as e:
        QMessageBox.critical(parent, "Error al exportar", str(e))



def fade_in(widget, duration=300):
    """
    Aplica una animación de fade-in a un widget.
    """
    widget.setWindowOpacity(0)
    widget.show()
    anim = QPropertyAnimation(widget, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(0)
    anim.setEndValue(1)
    anim.start()
    # Mantener referencia para que no se destruya
    widget._fade_anim = anim
