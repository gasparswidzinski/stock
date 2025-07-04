from PySide6.QtWidgets import (
    QDialog, QLineEdit, QTextEdit, QSpinBox, QPushButton, QFormLayout,
    QHBoxLayout, QListWidget, QMessageBox, QCompleter, QFileDialog
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6 import QtCore
from fancy_dialog import FancyDialog
from datetime import datetime
from utils import fade_in

class ItemDialog(FancyDialog):
    componente_guardado = Signal(int)

    def __init__(self, db, parent=None, comp_id=None):
        super().__init__(parent)
        self.db = db
        self.comp_id = comp_id
        self.setWindowTitle("Editar Componente" if comp_id else "Agregar Componente")
        self._build_ui()
        if comp_id:
            self._cargar_datos()
        fade_in(self)


    def _build_ui(self):
        layout = QFormLayout(self)
        self.edit_nombre = QLineEdit()
        layout.addRow("Nombre:", self.edit_nombre)
        self.edit_valor = QLineEdit()
        layout.addRow("Valor:", self.edit_valor)
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setMinimum(0)
        layout.addRow("Cantidad:", self.spin_cantidad)
        self.edit_ubicacion = QLineEdit()
        layout.addRow("Ubicación:", self.edit_ubicacion)
        self.text_descripcion = QTextEdit()
        layout.addRow("Descripción:", self.text_descripcion)
        self.edit_proveedor = QLineEdit()
        layout.addRow("Proveedor:", self.edit_proveedor)
        self.edit_fecha_compra = QLineEdit()
        self.edit_fecha_compra.setPlaceholderText("YYYY-MM-DD")
        layout.addRow("Fecha compra:", self.edit_fecha_compra)
        self.spin_stock_min = QSpinBox()
        self.spin_stock_min.setMinimum(0)
        layout.addRow("Stock mínimo:", self.spin_stock_min)
        self.edit_precio = QLineEdit()
        self.edit_precio.setPlaceholderText("Ej. 0.10")
        layout.addRow("Precio unitario:", self.edit_precio)

        # Campo y botón de imagen
        self.edit_imagen = QLineEdit()
        self.edit_imagen.setPlaceholderText("Ruta de la imagen...")
        btn_buscar_imagen = QPushButton("Seleccionar imagen...")
        btn_buscar_imagen.clicked.connect(self._seleccionar_imagen)
        h_imagen = QHBoxLayout()
        h_imagen.addWidget(self.edit_imagen)
        h_imagen.addWidget(btn_buscar_imagen)
        layout.addRow("Imagen:", h_imagen)

        etiquetas_existentes = self.db.obtener_todas_etiquetas()
        self.edit_nueva_etiqueta = QLineEdit()
        completer = QCompleter(etiquetas_existentes)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.edit_nueva_etiqueta.setCompleter(completer)
        btn_agregar_tag = QPushButton("Agregar etiqueta")
        btn_agregar_tag.clicked.connect(self._on_agregar_etiqueta)
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.edit_nueva_etiqueta)
        h_layout.addWidget(btn_agregar_tag)
        layout.addRow("Etiquetas:", h_layout)

        self.list_etiquetas = QListWidget()
        layout.addRow("", self.list_etiquetas)

        btn_guardar = QPushButton(QIcon("icons/save.png"), "Guardar")
        btn_guardar.setIconSize(QtCore.QSize(24, 24))
        btn_cancelar = QPushButton(QIcon("icons/cancel.png"), "Cancelar")
        btn_cancelar.setIconSize(QtCore.QSize(24, 24))
        btn_guardar.clicked.connect(self._on_guardar)
        btn_cancelar.clicked.connect(self.reject)
        h_btn = QHBoxLayout()
        h_btn.addWidget(btn_guardar)
        h_btn.addWidget(btn_cancelar)
        layout.addRow("", h_btn)

    def _seleccionar_imagen(self):
        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if ruta:
            self.edit_imagen.setText(ruta)

    def _cargar_datos(self):
        c = self.db.conn.cursor()
        c.execute("SELECT * FROM componentes WHERE id=?", (self.comp_id,))
        r = c.fetchone()
        if not r:
            QMessageBox.warning(self, "Error", "No se encontró el componente.")
            self.done(QDialog.Rejected)
            return
        row = dict(r)
        self.edit_nombre.setText(row.get("nombre", ""))
        self.edit_valor.setText(row.get("valor", "") or "")
        self.spin_cantidad.setValue(row.get("cantidad", 0) or 0)
        self.edit_ubicacion.setText(row.get("ubicacion", "") or "")
        self.text_descripcion.setPlainText(row.get("descripcion", "") or "")
        self.edit_proveedor.setText(row.get("proveedor", "") or "")
        self.edit_fecha_compra.setText(row.get("fecha_compra", "") or "")
        self.spin_stock_min.setValue(row.get("stock_minimo", 0) or 0)
        self.edit_imagen.setText(row.get("imagen_path", "") or "")
        precio = row.get("precio_unitario")
        if precio is not None:
            self.edit_precio.setText(str(precio))
        etiquetas = self.db.obtener_etiquetas_por_componente(self.comp_id)
        for tag in etiquetas:
            self.list_etiquetas.addItem(tag)

    @Slot()
    def _on_agregar_etiqueta(self):
        text = self.edit_nueva_etiqueta.text().strip()
        if text:
            for i in range(self.list_etiquetas.count()):
                if self.list_etiquetas.item(i).text().lower() == text.lower():
                    self.edit_nueva_etiqueta.clear()
                    return
            self.list_etiquetas.addItem(text)
            self.edit_nueva_etiqueta.clear()

    @Slot()
    def _on_guardar(self):
        nombre = self.edit_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre no puede estar vacío.")
            return
        datos = {
            "nombre": nombre,
            "valor": self.edit_valor.text().strip(),
            "cantidad": self.spin_cantidad.value(),
            "ubicacion": self.edit_ubicacion.text().strip(),
            "descripcion": self.text_descripcion.toPlainText().strip(),
            "proveedor": self.edit_proveedor.text().strip(),
            "fecha_compra": self.edit_fecha_compra.text().strip() or None,
            "stock_minimo": self.spin_stock_min.value(),
            "imagen_path": self.edit_imagen.text().strip() or None,
        }
        precio_text = self.edit_precio.text().strip()
        if precio_text:
            try:
                datos["precio_unitario"] = float(precio_text)
            except ValueError:
                QMessageBox.warning(self, "Validación", "Precio unitario inválido.")
                return
        else:
            datos["precio_unitario"] = None

        etiqueta_list = [self.list_etiquetas.item(i).text().strip() for i in range(self.list_etiquetas.count())]

        if self.comp_id:
            self.db.editar_componente(self.comp_id, datos, etiqueta_list)
            comp_id = self.comp_id
        else:
            comp_id = self.db.agregar_componente(datos, etiqueta_list)

        c = self.db.conn.cursor()
        accion = "Edición" if self.comp_id else "Alta"
        descripcion = "Edición de componente" if self.comp_id else "Nuevo componente agregado"
        c.execute("""
            INSERT INTO historial (componente_id, accion, cantidad, fecha_hora, descripcion)
            VALUES (?, ?, ?, ?, ?)
        """, (
            comp_id,
            accion,
            datos["cantidad"],
            datetime.now().isoformat(sep=" ", timespec="seconds"),
            descripcion
        ))
        self.db.conn.commit()
        self.componente_guardado.emit(comp_id)
        self.accept()
