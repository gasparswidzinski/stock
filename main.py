<<<<<<< HEAD
import sys
from PySide6.QtWidgets import QApplication
from mainwindow import MainWindow
=======
# main.py
import sys
import sqlite3
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QWidget, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QLineEdit, QLabel, QHBoxLayout, QDialog,
    QFormLayout, QComboBox, QTextEdit, QListWidget, QCompleter, QSpinBox, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QSettings, Signal, Slot
from PySide6.QtGui import QAction 




DB_FILENAME = "inventario_componentes.db"

def obtener_ruta_bd():
    # Puedes guarda en carpeta de usuario; aquí en el mismo directorio:
    return os.path.join(os.path.dirname(__file__), DB_FILENAME)

class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(obtener_ruta_bd())
        self.conn.row_factory = sqlite3.Row
        self._inicializar_bd()

    def _inicializar_bd(self):
        c = self.conn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS componentes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            valor TEXT,
            cantidad INTEGER NOT NULL DEFAULT 0,
            ubicacion TEXT,
            descripcion TEXT,
            proveedor TEXT,
            fecha_compra TEXT,
            stock_minimo INTEGER,
            precio_unitario REAL
        );
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS componentes_etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            componente_id INTEGER NOT NULL,
            etiqueta_id INTEGER NOT NULL,
            UNIQUE(componente_id, etiqueta_id),
            FOREIGN KEY(componente_id) REFERENCES componentes(id) ON DELETE CASCADE,
            FOREIGN KEY(etiqueta_id) REFERENCES etiquetas(id) ON DELETE CASCADE
        );
        ''')
        # Tabla movimientos si deseas
        self.conn.commit()

    def obtener_todas_etiquetas(self):
        c = self.conn.cursor()
        c.execute("SELECT nombre FROM etiquetas ORDER BY nombre COLLATE NOCASE;")
        return [row["nombre"] for row in c.fetchall()]

    def _agregar_etiqueta_si_no_existe(self, nombre):
        c = self.conn.cursor()
        try:
            c.execute("INSERT INTO etiquetas(nombre) VALUES (?)", (nombre,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # ya existía
        # Obtener el id:
        c.execute("SELECT id FROM etiquetas WHERE nombre=?", (nombre,))
        row = c.fetchone()
        return row["id"] if row else None

    def agregar_componente(self, datos: dict, lista_etiquetas: list[str]):
        """
        datos: dict con claves: nombre, valor, cantidad, ubicacion, descripcion, proveedor, fecha_compra, stock_minimo, precio_unitario
        lista_etiquetas: lista de strings
        """
        c = self.conn.cursor()
        campos = ", ".join(datos.keys())
        placeholders = ", ".join("?" for _ in datos)
        valores = tuple(datos.values())
        c.execute(f"INSERT INTO componentes({campos}) VALUES ({placeholders})", valores)
        comp_id = c.lastrowid
        for etiqueta in lista_etiquetas:
            et_id = self._agregar_etiqueta_si_no_existe(etiqueta)
            if et_id:
                try:
                    c.execute("INSERT INTO componentes_etiquetas(componente_id, etiqueta_id) VALUES (?,?)", (comp_id, et_id))
                except sqlite3.IntegrityError:
                    pass
        self.conn.commit()
        return comp_id

    def editar_componente(self, comp_id: int, datos: dict, lista_etiquetas: list[str]):
        c = self.conn.cursor()
        # Actualizar campos
        set_clause = ", ".join(f"{k}=?" for k in datos.keys())
        valores = tuple(datos.values()) + (comp_id,)
        c.execute(f"UPDATE componentes SET {set_clause} WHERE id=?", valores)
        # Gestionar etiquetas: borrar existentes y volver a insertar
        c.execute("DELETE FROM componentes_etiquetas WHERE componente_id=?", (comp_id,))
        for etiqueta in lista_etiquetas:
            et_id = self._agregar_etiqueta_si_no_existe(etiqueta)
            if et_id:
                try:
                    c.execute("INSERT INTO componentes_etiquetas(componente_id, etiqueta_id) VALUES (?,?)", (comp_id, et_id))
                except sqlite3.IntegrityError:
                    pass
        self.conn.commit()

    def eliminar_componente(self, comp_id: int):
        c = self.conn.cursor()
        c.execute("DELETE FROM componentes WHERE id=?", (comp_id,))
        self.conn.commit()

    def obtener_componentes_por_etiqueta(self, etiqueta: str):
        c = self.conn.cursor()
        c.execute('''
        SELECT c.* FROM componentes c
        JOIN componentes_etiquetas ce ON c.id=ce.componente_id
        JOIN etiquetas e ON ce.etiqueta_id=e.id
        WHERE e.nombre=?
        ORDER BY c.nombre COLLATE NOCASE;
        ''', (etiqueta,))
        return [dict(row) for row in c.fetchall()]

    def obtener_componentes_todos(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM componentes ORDER BY nombre COLLATE NOCASE;")
        return [dict(row) for row in c.fetchall()]

    def obtener_etiquetas_por_componente(self, comp_id: int):
        c = self.conn.cursor()
        c.execute('''
        SELECT e.nombre FROM etiquetas e
        JOIN componentes_etiquetas ce ON e.id=ce.etiqueta_id
        WHERE ce.componente_id=?
        ''', (comp_id,))
        return [row["nombre"] for row in c.fetchall()]

    # Métodos extra: buscar, historial, renombrar/eliminar etiqueta...

class ItemDialog(QDialog):
    componente_guardado = Signal(int)  # emitirá el id cuando se agregue o edite
    def __init__(self, db: DBManager, parent=None, comp_id=None):
        super().__init__(parent)
        self.db = db
        self.comp_id = comp_id  # si None, es nuevo; si no, editar
        self.setWindowTitle("Editar Componente" if comp_id else "Agregar Componente")
        self._build_ui()
        if comp_id:
            self._cargar_datos()

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
        # Fecha de compra: por simplicidad Text; ideal QDateEdit
        self.edit_fecha_compra = QLineEdit()
        self.edit_fecha_compra.setPlaceholderText("YYYY-MM-DD")
        layout.addRow("Fecha compra:", self.edit_fecha_compra)
        self.spin_stock_min = QSpinBox()
        self.spin_stock_min.setMinimum(0)
        layout.addRow("Stock mínimo:", self.spin_stock_min)
        self.edit_precio = QLineEdit()
        self.edit_precio.setPlaceholderText("Ej. 0.10")
        layout.addRow("Precio unitario:", self.edit_precio)
        # Etiquetas: QLineEdit con QCompleter y un QListWidget para mostrar las agregadas:
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
        # Botones Guardar/Cancelar
        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self._on_guardar)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        h_btn = QHBoxLayout()
        h_btn.addWidget(btn_guardar)
        h_btn.addWidget(btn_cancelar)
        layout.addRow("", h_btn)

    def _cargar_datos(self):
        # Cargar datos desde BD para comp_id
        # Suponemos que dbManager puede devolver un dict con claves
        row = None
        # Hacemos SELECT
        c = self.db.conn.cursor()
        c.execute("SELECT * FROM componentes WHERE id=?", (self.comp_id,))
        r = c.fetchone()
        if r:
            row = dict(r)
        if not row:
            QMessageBox.warning(self, "Error", "No se encontró el componente.")
            self.reject()
            return
        self.edit_nombre.setText(row.get("nombre",""))
        self.edit_valor.setText(row.get("valor","") or "")
        self.spin_cantidad.setValue(row.get("cantidad",0) or 0)
        self.edit_ubicacion.setText(row.get("ubicacion","") or "")
        self.text_descripcion.setPlainText(row.get("descripcion","") or "")
        self.edit_proveedor.setText(row.get("proveedor","") or "")
        self.edit_fecha_compra.setText(row.get("fecha_compra","") or "")
        self.spin_stock_min.setValue(row.get("stock_minimo",0) or 0)
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
            # Evitar duplicados
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
        # Emitir señal para notificar a MainWindow que cree/actualice docks
        self.componente_guardado.emit(comp_id)
        self.accept()

class TagDockWidget(QDockWidget):
    def __init__(self, etiqueta: str, db: DBManager, parent=None):
        super().__init__(etiqueta, parent)
        self.etiqueta = etiqueta
        self.db = db
        self.setObjectName(f"Dock_{etiqueta}")  # para guardar estado en QSettings
        self.widget = QWidget()
        self.setWidget(self.widget)
        v = QVBoxLayout(self.widget)
        # Filtro interno
        filtro_layout = QHBoxLayout()
        filtro_layout.addWidget(QLabel("Filtro:"))
        self.edit_filtro = QLineEdit()
        self.edit_filtro.textChanged.connect(self._on_filtrar)
        filtro_layout.addWidget(self.edit_filtro)
        v.addLayout(filtro_layout)
        # Tabla de componentes
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID","Nombre","Cantidad","Ubicación"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        v.addWidget(self.table)
        # Botones rápidos: Editar / Eliminar
        btn_layout = QHBoxLayout()
        btn_editar = QPushButton("Editar")
        btn_editar.clicked.connect(self._editar_seleccionado)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(self._eliminar_seleccionado)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_eliminar)
        v.addLayout(btn_layout)
        self._cargar_items()

    def _cargar_items(self):
        # Obtener datos de BD
        items = self.db.obtener_componentes_por_etiqueta(self.etiqueta)
        self._full_items = items  # lista completa
        self._mostrar_items(items)

    def _mostrar_items(self, items: list[dict]):
        self.table.setRowCount(0)
        for row_data in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(row_data["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(row_data["nombre"]))
            self.table.setItem(row, 2, QTableWidgetItem(str(row_data["cantidad"])))
            self.table.setItem(row, 3, QTableWidgetItem(row_data.get("ubicacion","") or ""))
        self.table.resizeColumnsToContents()

    @Slot()
    def actualizar_lista(self):
        self._cargar_items()

    @Slot(str)
    def _on_filtrar(self, texto):
        texto = texto.lower()
        filtrados = []
        for item in self._full_items:
            # Filtrar por nombre o ubicación o valor en futuro
            if texto in item["nombre"].lower() or texto in (item.get("ubicacion","") or "").lower():
                filtrados.append(item)
        self._mostrar_items(filtrados)

    @Slot()
    def _editar_seleccionado(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        comp_id = int(self.table.item(row, 0).text())
        dlg = ItemDialog(self.db, parent=self, comp_id=comp_id)
        dlg.componente_guardado.connect(self._on_item_guardado_externo)
        if dlg.exec():
            # tras editar, recargar
            self.actualizar_lista()
            # Notificar MainWindow para actualizar otros docks si cambió etiquetas
            self.parent().on_componente_guardado(comp_id)

    @Slot()
    def _eliminar_seleccionado(self):
        selected = self.table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        comp_id = int(self.table.item(row, 0).text())
        resp = QMessageBox.question(self, "Confirmar", f"¿Eliminar componente ID {comp_id}?")
        if resp == QMessageBox.Yes:
            self.db.eliminar_componente(comp_id)
            self.actualizar_lista()
            # Notificar MainWindow
            self.parent().on_componente_eliminado(comp_id)

    @Slot(int)
    def _on_item_guardado_externo(self, comp_id):
        # Si se edita desde otro lugar, recargar si pertenece a esta etiqueta
        self.actualizar_lista()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Stock de Componentes")
        self.db = DBManager()
        # Mantener dict de docks: etiqueta -> TagDockWidget
        self.docks: dict[str, TagDockWidget] = {}
        # Menú y toolbar
        self._build_actions()
        # Restaurar estado guardado
        self._restore_ui_state()

    def _build_actions(self):
        menubar = self.menuBar()
        menu_archivo = menubar.addMenu("Archivo")
        act_agregar = QAction("Agregar componente", self)
        act_agregar.triggered.connect(self._on_agregar_componente)
        menu_archivo.addAction(act_agregar)
        act_salir = QAction("Salir", self)
        act_salir.triggered.connect(self.close)
        menu_archivo.addAction(act_salir)

        menu_ver = menubar.addMenu("Ver")
        act_ver_etiquetas = QAction("Administrar etiquetas", self)
        act_ver_etiquetas.triggered.connect(self._on_administrar_etiquetas)
        menu_ver.addAction(act_ver_etiquetas)

        # Barra de herramientas con búsqueda global
        toolbar = self.addToolBar("Principal")
        self.edit_buscar = QLineEdit()
        self.edit_buscar.setPlaceholderText("Buscar...")
        self.edit_buscar.returnPressed.connect(self._on_buscar_global)
        toolbar.addWidget(self.edit_buscar)
        btn_buscar = QAction("Buscar", self)
        btn_buscar.triggered.connect(self._on_buscar_global)
        toolbar.addAction(btn_buscar)

    @Slot()
    def _on_agregar_componente(self):
        dlg = ItemDialog(self.db, parent=self)
        dlg.componente_guardado.connect(self.on_componente_guardado)
        dlg.exec()

    @Slot(int)
    def on_componente_guardado(self, comp_id: int):
        # Cuando se agrega o edita un componente: obtener sus etiquetas actuales y actualizar docks
        etiquetas = self.db.obtener_etiquetas_por_componente(comp_id)
        # 1) Para cada etiqueta: si no hay dock, crear; si hay, actualizar.
        for tag in etiquetas:
            if tag not in self.docks:
                dock = TagDockWidget(tag, self.db, parent=self)
                self.addDockWidget(Qt.RightDockWidgetArea, dock)
                self.docks[tag] = dock
            else:
                dock = self.docks[tag]
            dock.actualizar_lista()
        # 2) También es posible que se hayan quitado etiquetas: recorrer docks existentes y verificar si el componente aún pertenece; si no, actualizar; si dock queda vacío, opcional cerrar.
        for tag, dock in list(self.docks.items()):
            if tag not in etiquetas:
                # recargar lista para remover fila si existía
                dock.actualizar_lista()
                # Si ya no hay componentes con esta etiqueta, cerrar dock
                items = self.db.obtener_componentes_por_etiqueta(tag)
                if not items:
                    dock.close()
                    del self.docks[tag]
        # (Opcional) actualizar vista global si existe

    @Slot(int)
    def on_componente_eliminado(self, comp_id: int):
        # Similar a editar sin etiquetas: borrar de cada dock si existía; si queda vacío, cerrar dock.
        for tag, dock in list(self.docks.items()):
            items = self.db.obtener_componentes_por_etiqueta(tag)
            if not items:
                dock.close()
                del self.docks[tag]
            else:
                dock.actualizar_lista()

    @Slot()
    def _on_buscar_global(self):
        texto = self.edit_buscar.text().strip().lower()
        if not texto:
            return
        # Buscar en nombre, valor, descripcion, ubicacion, proveedor; y también etiquetas
        c = self.db.conn.cursor()
        # Búsqueda simple con LIKE:
        pattern = f"%{texto}%"
        c.execute('''
        SELECT DISTINCT c.* FROM componentes c
        LEFT JOIN componentes_etiquetas ce ON c.id=ce.componente_id
        LEFT JOIN etiquetas e ON ce.etiqueta_id=e.id
        WHERE LOWER(c.nombre) LIKE ?
           OR LOWER(c.valor) LIKE ?
           OR LOWER(c.descripcion) LIKE ?
           OR LOWER(c.ubicacion) LIKE ?
           OR LOWER(c.proveedor) LIKE ?
           OR LOWER(e.nombre) LIKE ?
        ORDER BY c.nombre COLLATE NOCASE;
        ''', (pattern,pattern,pattern,pattern,pattern,pattern))
        resultados = [dict(r) for r in c.fetchall()]
        # Mostrar en un diálogo sencillo
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Resultados de búsqueda: '{texto}'")
        v = QVBoxLayout(dlg)
        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["ID","Nombre","Etiquetas"])
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        for row_data in resultados:
            row = tabla.rowCount()
            tabla.insertRow(row)
            tabla.setItem(row, 0, QTableWidgetItem(str(row_data["id"])))
            tabla.setItem(row, 1, QTableWidgetItem(row_data["nombre"]))
            etiquetas = self.db.obtener_etiquetas_por_componente(row_data["id"])
            tabla.setItem(row, 2, QTableWidgetItem(", ".join(etiquetas)))
        tabla.resizeColumnsToContents()
        v.addWidget(tabla)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dlg.accept)
        btn_editar = QPushButton("Editar seleccionado")
        def editar_sel():
            sel = tabla.selectedItems()
            if not sel:
                return
            comp_id = int(tabla.item(sel[0].row(), 0).text())
            dlg2 = ItemDialog(self.db, parent=self, comp_id=comp_id)
            dlg2.componente_guardado.connect(self.on_componente_guardado)
            dlg2.exec()
            # tras editar, recargar búsqueda
            dlg.accept()
            self._on_buscar_global()
        btn_editar.clicked.connect(editar_sel)
        h = QHBoxLayout()
        h.addWidget(btn_editar)
        h.addWidget(btn_cerrar)
        v.addLayout(h)
        dlg.resize(500, 300)
        dlg.exec()

    @Slot()
    def _on_administrar_etiquetas(self):
        # Podrías implementar un diálogo que liste todas las etiquetas y permita renombrar o eliminar.
        etiquetas = self.db.obtener_todas_etiquetas()
        dlg = QDialog(self)
        dlg.setWindowTitle("Administrar etiquetas")
        v = QVBoxLayout(dlg)
        listw = QListWidget()
        listw.addItems(etiquetas)
        v.addWidget(listw)
        btn_renombrar = QPushButton("Renombrar")
        btn_eliminar = QPushButton("Eliminar")
        btn_cerrar = QPushButton("Cerrar")
        def renombrar():
            sel = listw.selectedItems()
            if not sel: return
            old = sel[0].text()
            nuevo, ok = QInputDialog.getText(self, "Renombrar etiqueta", f"Nuevo nombre para '{old}':")
            if ok and nuevo.strip():
                # Actualizar en BD
                c = self.db.conn.cursor()
                try:
                    c.execute("UPDATE etiquetas SET nombre=? WHERE nombre=?", (nuevo.strip(), old))
                    self.db.conn.commit()
                    # Actualizar título de dock si existe
                    if old in self.docks:
                        dock = self.docks.pop(old)
                        dock.etiqueta = nuevo.strip()
                        dock.setWindowTitle(nuevo.strip())
                        dock.setObjectName(f"Dock_{nuevo.strip()}")
                        self.docks[nuevo.strip()] = dock
                    # Actualizar lista en diálogo
                    sel[0].setText(nuevo.strip())
                except sqlite3.IntegrityError:
                    QMessageBox.warning(self, "Error", "Ya existe una etiqueta con ese nombre.")
        def eliminar():
            sel = listw.selectedItems()
            if not sel: return
            tag = sel[0].text()
            resp = QMessageBox.question(self, "Confirmar", f"Eliminar etiqueta '{tag}' de todos los componentes?")
            if resp == QMessageBox.Yes:
                # Borrar de BD: ON DELETE CASCADE eliminará relaciones
                c = self.db.conn.cursor()
                c.execute("DELETE FROM etiquetas WHERE nombre=?", (tag,))
                self.db.conn.commit()
                # Cerrar dock si existe
                if tag in self.docks:
                    dock = self.docks.pop(tag)
                    dock.close()
                listw.takeItem(listw.row(sel[0]))
        btn_renombrar.clicked.connect(renombrar)
        btn_eliminar.clicked.connect(eliminar)
        h = QHBoxLayout()
        h.addWidget(btn_renombrar)
        h.addWidget(btn_eliminar)
        h.addWidget(btn_cerrar)
        v.addLayout(h)
        btn_cerrar.clicked.connect(dlg.accept)
        dlg.resize(300, 400)
        dlg.exec()

    def closeEvent(self, event):
        # Guardar estado de UI
        settings = QSettings("MiInventario", "AppStock")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

    def _restore_ui_state(self):
        settings = QSettings("MiInventario", "AppStock")
        geom = settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
        # No restauramos docks de etiquetas porque al iniciar no sabemos qué docks existían.
        # Podríamos guardar la lista de etiquetas abiertas en settings y recrearlas:
        etiquetas = self.db.obtener_todas_etiquetas()
        # Por ejemplo, si quieres restaurar docks abiertos, guarda en settings una lista de etiquetas abiertas.
        # Para versión inicial, dejamos que el usuario abra docks manualmente (al agregar o desde Buscar).
        # Si prefieres restaurarlos:
        # open_tags = settings.value("openTags", [])
        # for tag in open_tags: crear dock igual que en on_componente_guardado
>>>>>>> bd01dda89ec0c51c206ac37eaebb97131f8f7bd2

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
<<<<<<< HEAD
    sys.exit(app.exec())
#anal
=======
    sys.exit(app.exec())
>>>>>>> bd01dda89ec0c51c206ac37eaebb97131f8f7bd2
