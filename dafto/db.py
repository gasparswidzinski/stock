import sqlite3
import os

DB_FILENAME = "inventario_componentes.db"

def obtener_ruta_bd():
    return os.path.join(os.path.dirname(__file__), DB_FILENAME)

class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(obtener_ruta_bd())
        self.conn.row_factory = sqlite3.Row
        self._inicializar_bd()

    def _inicializar_bd(self):
        c = self.conn.cursor()
        c.executescript('''
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
        CREATE TABLE IF NOT EXISTS etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS componentes_etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            componente_id INTEGER NOT NULL,
            etiqueta_id INTEGER NOT NULL,
            UNIQUE(componente_id, etiqueta_id),
            FOREIGN KEY(componente_id) REFERENCES componentes(id) ON DELETE CASCADE,
            FOREIGN KEY(etiqueta_id) REFERENCES etiquetas(id) ON DELETE CASCADE
        );
        
        
        ''')
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
            pass
        c.execute("SELECT id FROM etiquetas WHERE nombre=?", (nombre,))
        row = c.fetchone()
        return row["id"] if row else None

    def agregar_componente(self, datos, lista_etiquetas):
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

    def editar_componente(self, comp_id, datos, lista_etiquetas):
        c = self.conn.cursor()
        set_clause = ", ".join(f"{k}=?" for k in datos.keys())
        valores = tuple(datos.values()) + (comp_id,)
        c.execute(f"UPDATE componentes SET {set_clause} WHERE id=?", valores)
        c.execute("DELETE FROM componentes_etiquetas WHERE componente_id=?", (comp_id,))
        for etiqueta in lista_etiquetas:
            et_id = self._agregar_etiqueta_si_no_existe(etiqueta)
            if et_id:
                try:
                    c.execute("INSERT INTO componentes_etiquetas(componente_id, etiqueta_id) VALUES (?,?)", (comp_id, et_id))
                except sqlite3.IntegrityError:
                    pass
        self.conn.commit()

    def eliminar_componente(self, comp_id):
        c = self.conn.cursor()
        c.execute("DELETE FROM componentes WHERE id=?", (comp_id,))
        self.conn.commit()

    def obtener_componentes_por_etiqueta(self, etiqueta):
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

    def obtener_etiquetas_por_componente(self, comp_id):
        c = self.conn.cursor()
        c.execute('''
        SELECT e.nombre FROM etiquetas e
        JOIN componentes_etiquetas ce ON e.id=ce.etiqueta_id
        WHERE ce.componente_id=?
        ''', (comp_id,))
        return [row["nombre"] for row in c.fetchall()]
    
    def obtener_componente_por_id(self, comp_id):
        c = self.conn.cursor()
        c.execute("SELECT * FROM componentes WHERE id=?", (comp_id,))
        return dict(c.fetchone())
    
    def guardar_proyecto(self, nombre, tipo, lista_componentes):
        c = self.conn.cursor()
        c.execute("INSERT INTO proyectos(nombre, fecha, tipo) VALUES (?, date('now'), ?)", (nombre, tipo))
        proyecto_id = c.lastrowid
        for comp in lista_componentes:
            c.execute("INSERT INTO proyectos_componentes(proyecto_id, componente_id, cantidad) VALUES (?, ?, ?)",
                    (proyecto_id, comp["id"], comp["cantidad"]))
        self.conn.commit()
    
    def soldar_proyecto(self, nombre, lista_componentes):
        c = self.conn.cursor()
        faltantes = []
        for comp in lista_componentes:
            c.execute("SELECT cantidad, nombre FROM componentes WHERE id=?", (comp["id"],))
            row = c.fetchone()
            if not row or row["cantidad"] < comp["cantidad"]:
                faltantes.append(row["nombre"] if row else f"ID {comp['id']}")
        if faltantes:
            return False, faltantes

        for comp in lista_componentes:
            c.execute("UPDATE componentes SET cantidad = cantidad - ? WHERE id=?", (comp["cantidad"], comp["id"]))
    
        c.execute("INSERT INTO proyectos(nombre, fecha, tipo) VALUES (?, date('now'), ?)", (nombre, "soldado"))
        proyecto_id = c.lastrowid
        for comp in lista_componentes:
            c.execute("INSERT INTO proyectos_componentes(proyecto_id, componente_id, cantidad) VALUES (?, ?, ?)",
                    (proyecto_id, comp["id"], comp["cantidad"]))
        self.conn.commit()
        return True, []