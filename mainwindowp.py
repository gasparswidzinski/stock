from PySide6.QtWidgets import (
    QMainWindow, QLineEdit, QDialog, QVBoxLayout, QTableWidget,
    QTableWidgetItem, QPushButton, QHBoxLayout, QListWidget, QMessageBox, QInputDialog,
    QLabel, QDialogButtonBox, QFileDialog
)
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtCore import Qt, QSettings, Slot
from db import DBManager
from dialogs import ItemDialog
from docks import TagDockWidget
from proyectos import ProyectoWidget
from proyectos_dialog import ProyectosDialog
from dashboard import DashboardWidget
from utils import cargar_tema, exportar_csv, exportar_excel
from PySide6.QtGui import QAction, QKeySequence, QIcon, QShortcut


class MainWindow(QMainWindow):
    """
    Ventana principal de la aplicación.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Control de Stock de Componentes")
        self.db = DBManager()
        self.docks = {}

        self._build_actions()
        self._restore_ui_state()
        self._abrir_etiquetas_existentes()
        self._alertar_stock_bajo()
        self._mostrar_dashboard()

        # Cargar tema dinámico según configuración
        settings = QSettings("MiInventario", "AppStock")
        tema = settings.value("tema", "Claro")
        color = settings.value("color_acento", "#4F81BD")
        fuente = settings.value("tam_fuente", "11pt")

        if tema == "Claro":
            cargar_tema(self, "tema_claro.qss", color, fuente)
        elif tema == "Oscuro":
            cargar_tema(self, "tema_oscuro.qss", color, fuente)
        else:
            cargar_tema(self, "tema_intermedio.qss", color, fuente)

    def _build_actions(self):
        """
        Construye menú, toolbar y atajos.
        """
        menubar = self.menuBar()
        menu_archivo = menubar.addMenu("Archivo")

        act_agregar = QAction(QIcon("icons/add.png"), "Agregar componente", self)
        act_agregar.triggered.connect(self._on_agregar_componente)
        act_agregar.setToolTip("Agregar un nuevo componente")
        menu_archivo.addAction(act_agregar)

        act_salir = QAction("Salir", self)
        act_salir.triggered.connect(self.close)
        act_salir.setToolTip("Cerrar la aplicación")
        menu_archivo.addAction(act_salir)

        toolbar = self.addToolBar("Principal")
        toolbar.setObjectName("Principal")

        self.edit_buscar = QLineEdit()
        self.edit_buscar.setPlaceholderText("Buscar...")
        self.edit_buscar.returnPressed.connect(self._on_buscar_global)
        toolbar.addWidget(self.edit_buscar)

        btn_buscar = QAction(QIcon("icons/inventory.png"), "Buscar", self)
        btn_buscar.triggered.connect(self._on_buscar_global)
        btn_buscar.setToolTip("Buscar componente por texto")
        toolbar.addAction(btn_buscar)

        shortcut_buscar = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_buscar.activated.connect(self._mostrar_dialogo_busqueda)

        menu_ver = menubar.addMenu("Ver")

        act_ver_etiquetas = QAction(QIcon("icons/folder.png"), "Administrar etiquetas", self)
        act_ver_etiquetas.triggered.connect(self._on_administrar_etiquetas)
        act_ver_etiquetas.setToolTip("Ver y gestionar etiquetas")
        menu_ver.addAction(act_ver_etiquetas)

        act_nuevo_proyecto = QAction(QIcon("icons/folder.png"), "Nuevo Proyecto", self)
        act_nuevo_proyecto.triggered.connect(self._nuevo_proyecto)
        act_nuevo_proyecto.setToolTip("Crear un nuevo proyecto")
        menu_ver.addAction(act_nuevo_proyecto)

        act_ver_proyectos = QAction(QIcon("icons/folder.png"), "Ver proyectos guardados", self)
        act_ver_proyectos.triggered.connect(self._abrir_dialogo_proyectos)
        act_ver_proyectos.setToolTip("Ver historial de proyectos")
        menu_ver.addAction(act_ver_proyectos)

        act_ver_historial = QAction(QIcon("icons/history.png"), "Ver historial de movimientos", self)
        act_ver_historial.triggered.connect(self._abrir_historial)
        act_ver_historial.setToolTip("Ver todos los movimientos de stock")
        menu_ver.addAction(act_ver_historial)

        act_configuracion = QAction(QIcon("icons/settings.png"), "Configuración visual", self)
        act_configuracion.triggered.connect(self._abrir_configuracion)
        act_configuracion.setToolTip("Cambiar tema, color y fuente")
        menu_ver.addAction(act_configuracion)

        # Atajos
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self._on_agregar_componente)
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self._nuevo_proyecto)
        QShortcut(QKeySequence("Ctrl+H"), self, activated=self._abrir_historial)
        QShortcut(QKeySequence("F3"), self, activated=self._entrada_rapida_stock)
        QShortcut(QKeySequence("F4"), self, activated=self._mostrar_todo_stock)

    def _mostrar_dashboard(self):
        """
        Panel principal.
        """
        dashboard = DashboardWidget(self.db, self)
        self.setCentralWidget(dashboard)

    @Slot()
    def _on_agregar_componente(self):
        """
        Agrega un componente.
        """
        dlg = ItemDialog(self.db, parent=self)
        dlg.componente_guardado.connect(self._refresh_vistas)
        dlg.exec()

    def _refresh_vistas(self):
        """
        Refresca etiquetas y dashboard.
        """
        self._abrir_etiquetas_existentes()
        self._mostrar_dashboard()
    @Slot()
    def _entrada_rapida_stock(self):
        """
        Entrada rápida de stock por ID.
        """
        comp_id_str, ok = QInputDialog.getText(self, "Entrada rápida de stock", "ID del componente:")
        if not ok or not comp_id_str.strip():
            return
        try:
            comp_id = int(comp_id_str.strip())
        except ValueError:
            QMessageBox.warning(self, "Error", "ID inválido.")
            return
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT nombre, cantidad FROM componentes WHERE id=?", (comp_id,))
        row = cursor.fetchone()
        if not row:
            QMessageBox.warning(self, "Error", "No se encontró el componente.")
            return
        cantidad_str, ok = QInputDialog.getText(
            self, "Cantidad a sumar",
            f"Componente: {row['nombre']} (Stock actual: {row['cantidad']})\nCantidad a sumar:"
        )
        if not ok or not cantidad_str.strip():
            return
        try:
            cantidad = int(cantidad_str.strip())
            if cantidad <= 0:
                raise ValueError()
        except ValueError:
            QMessageBox.warning(self, "Error", "Cantidad inválida.")
            return
        cursor.execute("UPDATE componentes SET cantidad = cantidad + ? WHERE id=?", (cantidad, comp_id))
        self.db.conn.commit()
        QMessageBox.information(
            self, "Stock actualizado",
            f"Nuevo stock de '{row['nombre']}': {row['cantidad'] + cantidad}"
        )
        self._refresh_vistas()

    @Slot()
    def _mostrar_todo_stock(self):
        """
        Muestra todos los componentes con opción de editar/eliminar.
        """
        from dialogs import ItemDialog
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM componentes")
        componentes = cursor.fetchall()
        if not componentes:
            QMessageBox.information(self, "Inventario vacío", "No hay componentes cargados.")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Inventario completo - Vista Detalle")
        layout = QVBoxLayout(dlg)

        tabla = QTableWidget()
        tabla.setColumnCount(7)
        tabla.setHorizontalHeaderLabels([
            "ID", "Etiqueta", "Nombre", "Cantidad", "Stock mínimo", "Ubicación", "Proveedor"
        ])
        tabla.setSelectionBehavior(QTableWidget.SelectRows)
        tabla.setSelectionMode(QTableWidget.ExtendedSelection)

        def cargar():
            tabla.setRowCount(0)
            cursor.execute("SELECT * FROM componentes")
            for row in cursor.fetchall():
                etiquetas = self.db.obtener_etiquetas_por_componente(row["id"])
                etiqueta = etiquetas[0] if etiquetas else "(Sin etiqueta)"
                row_pos = tabla.rowCount()
                tabla.insertRow(row_pos)
                tabla.setItem(row_pos, 0, QTableWidgetItem(str(row["id"])))
                tabla.setItem(row_pos, 1, QTableWidgetItem(etiqueta))
                tabla.setItem(row_pos, 2, QTableWidgetItem(row["nombre"]))
                item_cantidad = QTableWidgetItem(str(row["cantidad"]))
                if row["stock_minimo"] and row["cantidad"] < row["stock_minimo"]:
                    item_cantidad.setForeground(Qt.red)
                tabla.setItem(row_pos, 3, item_cantidad)
                tabla.setItem(row_pos, 4, QTableWidgetItem(str(row["stock_minimo"] or "-")))
                tabla.setItem(row_pos, 5, QTableWidgetItem(row["ubicacion"] or ""))
                tabla.setItem(row_pos, 6, QTableWidgetItem(row["proveedor"] or ""))

        cargar()
        layout.addWidget(tabla)

        btn_editar = QPushButton("Editar seleccionado")
        btn_eliminar = QPushButton("Eliminar seleccionados")
        btn_cerrar = QPushButton("Cerrar")

        def editar():
            sel = tabla.selectedItems()
            if not sel:
                return
            comp_id = int(tabla.item(sel[0].row(), 0).text())
            dlg_edit = ItemDialog(self.db, self, comp_id=comp_id)
            dlg_edit.componente_guardado.connect(cargar)
            dlg_edit.exec()
            self._refresh_vistas()

        def eliminar():
            selected = tabla.selectionModel().selectedRows()
            if not selected:
                return
            resp = QMessageBox.question(dlg, "Confirmar", f"Eliminar {len(selected)} componente(s)?")
            if resp != QMessageBox.Yes:
                return
            for idx in sorted(selected, key=lambda x: x.row(), reverse=True):
                comp_id = int(tabla.item(idx.row(), 0).text())
                self.db.eliminar_componente(comp_id)
            cargar()
            self._refresh_vistas()

        btn_editar.clicked.connect(editar)
        btn_eliminar.clicked.connect(eliminar)
        btn_cerrar.clicked.connect(dlg.accept)

        botones = QHBoxLayout()
        botones.addWidget(btn_editar)
        botones.addWidget(btn_eliminar)
        botones.addStretch()
        botones.addWidget(btn_cerrar)
        layout.addLayout(botones)

        dlg.resize(800, 500)
        dlg.exec()
    @Slot()
    def _abrir_historial(self):
        """
        Muestra el historial de movimientos.
        """
        from historial_dialog import HistorialDialog
        dlg = HistorialDialog(self.db, self)
        dlg.exec()

    @Slot()
    def _abrir_configuracion(self):
        """
        Abre configuración visual.
        """
        from configuracion_dialog import ConfiguracionDialog
        dlg = ConfiguracionDialog(self)
        dlg.exec()

    @Slot()
    def _abrir_dialogo_proyectos(self):
        """
        Muestra proyectos guardados.
        """
        dlg = ProyectosDialog(self.db, self)
        dlg.exec()

    @Slot()
    def _nuevo_proyecto(self):
        """
        Abre un nuevo proyecto.
        """
        widget = ProyectoWidget(self.db, self)
        self.setCentralWidget(widget)

    @Slot()
    def _mostrar_dialogo_busqueda(self):
        """
        Muestra la búsqueda avanzada.
        """
        from busqueda_avanzada_dialog import BusquedaAvanzadaDialog
        dlg = BusquedaAvanzadaDialog(self.db, self)
        dlg.exec()

    @Slot()
    def _on_buscar_global(self):
        """
        Ejecuta búsqueda rápida por texto.
        """
        texto = self.edit_buscar.text().strip().lower()
        if not texto:
            return
        from busqueda_avanzada_dialog import BusquedaAvanzadaDialog
        dlg = BusquedaAvanzadaDialog(self.db, self, filtro_rapido=texto)
        dlg.exec()

    def _abrir_etiquetas_existentes(self):
        """
        Abre etiquetas con componentes al iniciar.
        """
        etiquetas = self.db.obtener_todas_etiquetas()
        for tag in etiquetas:
            componentes = self.db.obtener_componentes_por_etiqueta(tag)
            if componentes and tag not in self.docks:
                dock = TagDockWidget(tag, self.db, parent=self)
                self.addDockWidget(Qt.RightDockWidgetArea, dock)
                self.docks[tag] = dock

    def _alertar_stock_bajo(self):
        """
        Muestra alerta si hay componentes bajo stock mínimo.
        """
        cursor = self.db.conn.cursor()
        cursor.execute("""
            SELECT nombre, cantidad, stock_minimo
            FROM componentes
            WHERE stock_minimo IS NOT NULL AND cantidad < stock_minimo
            ORDER BY nombre COLLATE NOCASE
        """)
        resultados = cursor.fetchall()
        if resultados:
            lista = "\n".join(
                f"{r['nombre']} (Stock: {r['cantidad']}, Mínimo: {r['stock_minimo']})"
                for r in resultados
            )
            QMessageBox.warning(
                self,
                "Stock bajo",
                f"Los siguientes componentes tienen stock por debajo del mínimo:\n\n{lista}"
            )

    def _restore_ui_state(self):
        """
        Restaura geometría y estado de docks.
        """
        settings = QSettings("MiInventario", "AppStock")
        geom = settings.value("geometry")
        if geom:
            self.restoreGeometry(geom)
        state = settings.value("windowState")
        if state:
            self.restoreState(state)

    def closeEvent(self, event):
        """
        Guarda estado antes de cerrar.
        """
        settings = QSettings("MiInventario", "AppStock")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)
    
    @Slot()
    def _on_administrar_etiquetas(self):
            """
            Muestra el diálogo para gestionar etiquetas.
            """
            etiquetas = self.db.obtener_todas_etiquetas()
            dlg = QDialog(self)
            dlg.setWindowTitle("Administrar etiquetas")
            v = QVBoxLayout(dlg)
            listw = QListWidget()
            listw.addItems(etiquetas)
            v.addWidget(listw)

            def renombrar():
                sel = listw.selectedItems()
                if not sel:
                    return
                old = sel[0].text()
                nuevo, ok = QInputDialog.getText(self, "Renombrar etiqueta", f"Nuevo nombre para '{old}':")
                if ok and nuevo.strip():
                    try:
                        self.db.renombrar_etiqueta(old, nuevo.strip())
                        sel[0].setText(nuevo.strip())
                        self._abrir_etiquetas_existentes()
                    except Exception as e:
                        QMessageBox.warning(self, "Error", str(e))

            def eliminar():
                sel = listw.selectedItems()
                if not sel:
                    return
                tag = sel[0].text()
                resp = QMessageBox.question(
                    self, "Confirmar eliminación",
                    f"¿Eliminar la etiqueta '{tag}' de todos los componentes?"
                )
                if resp == QMessageBox.Yes:
                    self.db.eliminar_etiqueta(tag)
                    listw.takeItem(listw.row(sel[0]))
                    self._abrir_etiquetas_existentes()

            btn_renombrar = QPushButton("Renombrar")
            btn_eliminar = QPushButton("Eliminar")
            btn_cerrar = QPushButton("Cerrar")
            btn_renombrar.clicked.connect(renombrar)
            btn_eliminar.clicked.connect(eliminar)
            btn_cerrar.clicked.connect(dlg.accept)

            h = QHBoxLayout()
            h.addWidget(btn_renombrar)
            h.addWidget(btn_eliminar)
            h.addWidget(btn_cerrar)
            v.addLayout(h)

            dlg.resize(300, 400)
            dlg.exec()
    @Slot()
    def _importar_proyecto_csv(self):
        """
        Importa componentes desde un CSV.
        """
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        import csv

        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar archivo CSV",
            "",
            "Archivos CSV (*.csv)"
        )
        if not ruta:
            return

        componentes = []
        try:
            with open(ruta, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader)
                for row in reader:
                    if len(row) < 2:
                        continue
                    comp_id = int(row[0].strip())
                    cantidad = int(row[1].strip())
                    if cantidad <= 0:
                        continue
                    componentes.append({"id": comp_id, "cantidad": cantidad})
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudo leer el archivo:\n{e}")
            return

        if not componentes:
            QMessageBox.warning(self, "Error", "El archivo no contiene datos válidos.")
            return

        widget = ProyectoWidget(self.db, self)
        widget.componentes = componentes
        widget._actualizar_tabla()
        self.setCentralWidget(widget)

