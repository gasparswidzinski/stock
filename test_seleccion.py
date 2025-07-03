from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
import sys

class TestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test selección múltiple")

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setRowCount(10)
        self.table.setHorizontalHeaderLabels(["Columna 1", "Columna 2"])

        # Datos de ejemplo
        for row in range(10):
            self.table.setItem(row, 0, QTableWidgetItem(f"Item {row+1}"))
            self.table.setItem(row, 1, QTableWidgetItem(f"Valor {row+1}"))

        # ⚠️ ESTA ES LA PARTE CLAVE:
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.MultiSelection)

        layout.addWidget(self.table)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TestWidget()
    w.resize(400, 300)
    w.show()
    sys.exit(app.exec())
