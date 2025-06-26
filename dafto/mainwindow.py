from PySide6.QtWidgets import (
    QMainWindow, QLineEdit, QDialog, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QListWidget, QMessageBox, QInputDialog,QLabel, QDialogButtonBox
)
from PySide6.QtGui import QAction
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt, QSettings, Slot
from db import DBManager
from dialogs import ItemDialog
from docks import TagDockWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Stock de Componentes")
        self.db = DBManager()
        self.docks = {}
        self._build_actions()
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


        toolbar = self.addToolBar("Principal")
        self.edit_buscar = QLineEdit()
        self.edit_buscar.setPlaceholderText("Buscar...")
        self.edit_buscar.returnPressed.connect(self._on_buscar_global)
        toolbar.addWidget(self.edit_buscar)
        btn_buscar = QAction("Buscar", self)
        btn_buscar.triggered.connect(self._on_buscar_global)
        toolbar.addAction(btn_buscar)
        shortcut_buscar = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_buscar.activated.connect(self._mostrar_dialogo_busqueda)
        
        menu_ver = menubar.addMenu("Ver")
       
        act_ver_etiquetas = QAction("Administrar etiquetas", self)
        act_ver_etiquetas.triggered.connect(self._on_administrar_etiquetas)
        menu_ver.addAction(act_ver_etiquetas)
       
        act_tema_oscuro = QAction("Activar tema oscuro", self)
        act_tema_oscuro.triggered.connect(self.aplicar_tema_oscuro)
        menu_ver.addAction(act_tema_oscuro)
        
        act_tema_claro = QAction("Volver al tema claro", self)
        act_tema_claro.triggered.connect(self.aplicar_tema_claro)
        menu_ver.addAction(act_tema_claro)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Insert:
            self._on_agregar_componente()
        else:
            super().keyPressEvent(event)   

    
    def _mostrar_dialogo_busqueda(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Buscar componente")
        layout = QVBoxLayout(dlg)

        label = QLabel("Ingrese el texto a buscar:")
        layout.addWidget(label)

        input_buscar = QLineEdit()
        layout.addWidget(input_buscar)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(botones)

        botones.accepted.connect(dlg.accept)
        botones.rejected.connect(dlg.reject)

        if dlg.exec():
            texto = input_buscar.text().strip()
            self._on_buscar_global(texto)

    @Slot()
    def _on_agregar_componente(self):
        dlg = ItemDialog(self.db, parent=self)
        dlg.componente_guardado.connect(self.on_componente_guardado)
        dlg.exec()

    @Slot(int)
    def on_componente_guardado(self, comp_id: int):
        etiquetas = self.db.obtener_etiquetas_por_componente(comp_id)
        for tag in etiquetas:
            if tag not in self.docks:
                dock = TagDockWidget(tag, self.db, parent=self)
                self.addDockWidget(Qt.RightDockWidgetArea, dock)
                self.docks[tag] = dock
            else:
                dock = self.docks[tag]
            dock.actualizar_lista()

        for tag, dock in list(self.docks.items()):
            if tag not in etiquetas:
                dock.actualizar_lista()
                if not self.db.obtener_componentes_por_etiqueta(tag):
                    dock.close()
                    del self.docks[tag]

    @Slot(int)
    def on_componente_eliminado(self, comp_id: int):
        for tag, dock in list(self.docks.items()):
            items = self.db.obtener_componentes_por_etiqueta(tag)
            if not items:
                dock.close()
                del self.docks[tag]
            else:
                dock.actualizar_lista()

    @Slot()
    @Slot(str)
    def _on_buscar_global(self, texto=None):
        if texto is None:
            texto = self.edit_buscar.text().strip().lower()
        else:
            texto = texto.lower()
        if not texto:
            return

        pattern = f"%{texto}%"
        c = self.db.conn.cursor()
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
        ''', (pattern,) * 6)
        resultados = [dict(r) for r in c.fetchall()]

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Resultados de búsqueda: '{texto}'")
        v = QVBoxLayout(dlg)
        tabla = QTableWidget()
        tabla.setColumnCount(3)
        tabla.setHorizontalHeaderLabels(["ID", "Nombre", "Etiquetas"])
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

        btn_editar = QPushButton("Editar seleccionado")
        def editar_sel():
            sel = tabla.selectedItems()
            if not sel:
                return
            comp_id = int(tabla.item(sel[0].row(), 0).text())
            dlg2 = ItemDialog(self.db, parent=self, comp_id=comp_id)
            dlg2.componente_guardado.connect(self.on_componente_guardado)
            dlg2.exec()
            dlg.accept()
            self._on_buscar_global()
        btn_editar.clicked.connect(editar_sel)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dlg.accept)
        h = QHBoxLayout()
        h.addWidget(btn_editar)
        h.addWidget(btn_cerrar)
        v.addLayout(h)
        dlg.resize(500, 300)
        dlg.exec()

    @Slot()
    def _on_administrar_etiquetas(self):
        etiquetas = self.db.obtener_todas_etiquetas()
        dlg = QDialog(self)
        dlg.setWindowTitle("Administrar etiquetas")
        v = QVBoxLayout(dlg)
        listw = QListWidget()
        listw.addItems(etiquetas)
        v.addWidget(listw)

        def renombrar():
            sel = listw.selectedItems()
            if not sel: return
            old = sel[0].text()
            nuevo, ok = QInputDialog.getText(self, "Renombrar etiqueta", f"Nuevo nombre para '{old}':")
            if ok and nuevo.strip():
                c = self.db.conn.cursor()
                try:
                    c.execute("UPDATE etiquetas SET nombre=? WHERE nombre=?", (nuevo.strip(), old))
                    self.db.conn.commit()
                    if old in self.docks:
                        dock = self.docks.pop(old)
                        dock.etiqueta = nuevo.strip()
                        dock.setWindowTitle(nuevo.strip())
                        dock.setObjectName(f"Dock_{nuevo.strip()}")
                        self.docks[nuevo.strip()] = dock
                    sel[0].setText(nuevo.strip())
                except:
                    QMessageBox.warning(self, "Error", "Ya existe una etiqueta con ese nombre.")

        def eliminar():
            sel = listw.selectedItems()
            if not sel: return
            tag = sel[0].text()
            resp = QMessageBox.question(self, "Confirmar", f"Eliminar etiqueta '{tag}' de todos los componentes?")
            if resp == QMessageBox.Yes:
                c = self.db.conn.cursor()
                c.execute("DELETE FROM etiquetas WHERE nombre=?", (tag,))
                self.db.conn.commit()
                if tag in self.docks:
                    dock = self.docks.pop(tag)
                    dock.close()
                listw.takeItem(listw.row(sel[0]))

        btn_renombrar = QPushButton("Renombrar")
        btn_renombrar.clicked.connect(renombrar)
        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.clicked.connect(eliminar)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dlg.accept)
        h = QHBoxLayout()
        h.addWidget(btn_renombrar)
        h.addWidget(btn_eliminar)
        h.addWidget(btn_cerrar)
        v.addLayout(h)
        dlg.resize(300, 400)
        dlg.exec()

    def closeEvent(self, event):
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
    
    def aplicar_tema_oscuro(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #e0e0e0;
            }
            QMenuBar, QMenu, QToolBar, QDialog, QLabel, QLineEdit, QTextEdit,
            QSpinBox, QListWidget, QPushButton, QTableWidget, QDockWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: none;
            }
            QLineEdit, QTextEdit, QSpinBox {
                border: 1px solid #333;
            }
            QPushButton {
                background-color: #2c2c2c;
                border: 1px solid #444;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
        """)
    def aplicar_tema_claro(self):
        self.setStyleSheet("")

