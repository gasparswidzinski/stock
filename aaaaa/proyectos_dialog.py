from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QLabel, QHeaderView
)
from PySide6.QtCore import Qt


class ProyectosDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Proyectos guardados")
        self.resize(700, 500)

        layout = QVBoxLayout(self)

        self.tabla_proyectos = QTableWidget()
        self.tabla_proyectos.setColumnCount(4)
        self.tabla_proyectos.setHorizontalHeaderLabels(["ID", "Nombre", "Fecha", "Tipo"])
        self.tabla_proyectos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_proyectos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_proyectos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Proyectos:"))
        layout.addWidget(self.tabla_proyectos)

        self.tabla_detalle = QTableWidget()
        self.tabla_detalle.setColumnCount(3)
        self.tabla_detalle.setHorizontalHeaderLabels(["ID", "Componente", "Cantidad"])
        self.tabla_detalle.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("Componentes del proyecto seleccionado:"))
        layout.addWidget(self.tabla_detalle)

        btn_exportar_csv = QPushButton("Exportar a CSV")
        btn_exportar_excel = QPushButton("Exportar a Excel")
        btn_cerrar = QPushButton("Cerrar")

        btn_exportar_csv.clicked.connect(self._exportar_csv)
        btn_exportar_excel.clicked.connect(self._exportar_excel)
        btn_cerrar.clicked.connect(self.accept)

        h = QHBoxLayout()
        h.addWidget(btn_exportar_csv)
        h.addWidget(btn_exportar_excel)
        h.addStretch()
        h.addWidget(btn_cerrar)
        layout.addLayout(h)
        
    def _cargar_proyectos(self):
        c = self.db.conn.cursor()
        c.execute("SELECT * FROM proyectos ORDER BY fecha DESC")
        proyectos = c.fetchall()
        self.tabla_proyectos.setRowCount(0)
        for p in proyectos:
            row = self.tabla_proyectos.rowCount()
            self.tabla_proyectos.insertRow(row)
            self.tabla_proyectos.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self.tabla_proyectos.setItem(row, 1, QTableWidgetItem(p["nombre"]))
            self.tabla_proyectos.setItem(row, 2, QTableWidgetItem(p["fecha"]))
            self.tabla_proyectos.setItem(row, 3, QTableWidgetItem(p["tipo"].capitalize()))

    def _mostrar_detalle(self):
        sel = self.tabla_proyectos.selectedItems()
        if not sel:
            return
        proyecto_id = int(self.tabla_proyectos.item(sel[0].row(), 0).text())
        c = self.db.conn.cursor()
        c.execute("""
            SELECT c.id, c.nombre, pc.cantidad
            FROM proyectos_componentes pc
            JOIN componentes c ON pc.componente_id = c.id
            WHERE pc.proyecto_id = ?
            ORDER BY c.nombre COLLATE NOCASE
        """, (proyecto_id,))
        componentes = c.fetchall()
        self.tabla_detalle.setRowCount(0)
        for r in componentes:
            row = self.tabla_detalle.rowCount()
            self.tabla_detalle.insertRow(row)
            self.tabla_detalle.setItem(row, 0, QTableWidgetItem(str(r["id"])))
            self.tabla_detalle.setItem(row, 1, QTableWidgetItem(r["nombre"]))
            self.tabla_detalle.setItem(row, 2, QTableWidgetItem(str(r["cantidad"])))
    
    def _exportar_csv(self):
        sel = self.tabla_proyectos.selectedItems()
        if not sel:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Seleccione un proyecto primero.")
            return

        proyecto_id = int(self.tabla_proyectos.item(sel[0].row(), 0).text())
        nombre_proyecto = self.tabla_proyectos.item(sel[0].row(), 1).text()

        import csv
        from PySide6.QtWidgets import QFileDialog

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar CSV",
            f"{nombre_proyecto}.csv",
            "Archivos CSV (*.csv)"
        )
        if not ruta:
            return

        c = self.db.conn.cursor()
        c.execute("""
            SELECT c.id, c.nombre, pc.cantidad
            FROM proyectos_componentes pc
            JOIN componentes c ON pc.componente_id = c.id
            WHERE pc.proyecto_id = ?
            ORDER BY c.nombre COLLATE NOCASE
        """, (proyecto_id,))
        componentes = c.fetchall()

        with open(ruta, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Componente", "Cantidad"])
            for r in componentes:
                writer.writerow([r["id"], r["nombre"], r["cantidad"]])

        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Exportación", "Archivo CSV exportado correctamente.")

    def _exportar_excel(self):
        sel = self.tabla_proyectos.selectedItems()
        if not sel:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", "Seleccione un proyecto primero.")
            return

        proyecto_id = int(self.tabla_proyectos.item(sel[0].row(), 0).text())
        nombre_proyecto = self.tabla_proyectos.item(sel[0].row(), 1).text()

        from PySide6.QtWidgets import QFileDialog
        from openpyxl import Workbook

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Excel",
            f"{nombre_proyecto}.xlsx",
            "Archivos Excel (*.xlsx)"
        )
        if not ruta:
            return

        c = self.db.conn.cursor()
        c.execute("""
            SELECT c.id, c.nombre, pc.cantidad
            FROM proyectos_componentes pc
            JOIN componentes c ON pc.componente_id = c.id
            WHERE pc.proyecto_id = ?
            ORDER BY c.nombre COLLATE NOCASE
        """, (proyecto_id,))
        componentes = c.fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Proyecto"

        ws.append(["ID", "Componente", "Cantidad"])
        for r in componentes:
            ws.append([r["id"], r["nombre"], r["cantidad"]])

        wb.save(ruta)

        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Exportación", "Archivo Excel exportado correctamente.")
