"""
Base de datos SQLite para NyPer.
Tablas: usuarios, ownership, cartera.
Archivo: data/nyper.db
"""

import os
import sqlite3
from datetime import datetime

import streamlit as st

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nyper.db")
_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "pablo.cuadros@bpba.com.ar")


@st.cache_resource
def _get_conn():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def inicializar_db():
    """Crea tablas si no existen. Inserta admin seed si la tabla está vacía."""
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            email TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'usuario',
            color TEXT NOT NULL DEFAULT '#00A651',
            activo INTEGER NOT NULL DEFAULT 1,
            codigo_afiliado TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            last_login TEXT
        );

        CREATE TABLE IF NOT EXISTS ownership (
            lead_id TEXT NOT NULL,
            sucursal_codigo TEXT NOT NULL,
            owner_email TEXT NOT NULL,
            fecha_toma TEXT NOT NULL,
            canal TEXT DEFAULT '',
            PRIMARY KEY (lead_id, sucursal_codigo),
            FOREIGN KEY (owner_email) REFERENCES usuarios(email)
        );

        CREATE TABLE IF NOT EXISTS cartera (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_email TEXT NOT NULL,
            nombre_razon_social TEXT NOT NULL,
            cuit TEXT DEFAULT '',
            rubro TEXT DEFAULT '',
            subrubro TEXT DEFAULT '',
            telefono TEXT DEFAULT '',
            mail TEXT DEFAULT '',
            direccion TEXT DEFAULT '',
            localidad TEXT DEFAULT '',
            observaciones TEXT DEFAULT '',
            nivel_paquete TEXT DEFAULT '',
            criterios_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (owner_email) REFERENCES usuarios(email)
        );
    """)
    conn.commit()

    # Migración: agregar columnas nuevas si no existen
    try:
        conn.execute("SELECT nivel_paquete FROM cartera LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE cartera ADD COLUMN nivel_paquete TEXT DEFAULT ''")
        conn.execute("ALTER TABLE cartera ADD COLUMN criterios_json TEXT DEFAULT '{}'")
        conn.commit()
    try:
        conn.execute("SELECT codigo_afiliado FROM usuarios LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE usuarios ADD COLUMN codigo_afiliado TEXT DEFAULT ''")
        conn.commit()

    # Admin seed
    admin = conn.execute("SELECT email FROM usuarios WHERE email = ?", (_ADMIN_EMAIL,)).fetchone()
    if not admin:
        from services.auth import _hash_password, _generar_salt
        salt = _generar_salt()
        pw_hash = _hash_password("nyper2026", salt)
        conn.execute(
            "INSERT INTO usuarios (email, nombre, apellido, password_hash, salt, rol, color, activo, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (_ADMIN_EMAIL, "Pablo", "Cuadros", pw_hash, salt, "admin", "#00A651", 1, datetime.now().isoformat()),
        )
        conn.commit()


# ── Usuarios ─────────────────────────────────────────────────────────────────

def obtener_usuario(email: str) -> dict | None:
    row = _get_conn().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def crear_usuario(email: str, nombre: str, apellido: str, password: str, rol: str = "usuario", color: str = "#3b82f6") -> bool:
    from services.auth import _hash_password, _generar_salt
    salt = _generar_salt()
    pw_hash = _hash_password(password, salt)
    try:
        _get_conn().execute(
            "INSERT INTO usuarios (email, nombre, apellido, password_hash, salt, rol, color, activo, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (email, nombre, apellido, pw_hash, salt, rol, color, 1, datetime.now().isoformat()),
        )
        _get_conn().commit()
        return True
    except sqlite3.IntegrityError:
        return False


def listar_usuarios() -> list[dict]:
    rows = _get_conn().execute("SELECT email, nombre, apellido, rol, color, activo, codigo_afiliado, created_at, last_login FROM usuarios ORDER BY nombre").fetchall()
    return [dict(r) for r in rows]


def actualizar_usuario(email: str, **campos) -> bool:
    permitidos = {"nombre", "apellido", "rol", "color", "activo", "last_login", "codigo_afiliado"}
    campos_filtrados = {k: v for k, v in campos.items() if k in permitidos}
    if not campos_filtrados:
        return False
    sets = ", ".join(f"{k} = ?" for k in campos_filtrados)
    vals = list(campos_filtrados.values()) + [email]
    _get_conn().execute(f"UPDATE usuarios SET {sets} WHERE email = ?", vals)
    _get_conn().commit()
    return True


def cambiar_password(email: str, nueva_password: str) -> bool:
    from services.auth import _hash_password, _generar_salt
    salt = _generar_salt()
    pw_hash = _hash_password(nueva_password, salt)
    _get_conn().execute("UPDATE usuarios SET password_hash = ?, salt = ? WHERE email = ?", (pw_hash, salt, email))
    _get_conn().commit()
    return True


# ── Ownership ────────────────────────────────────────────────────────────────

def registrar_ownership(lead_id: str, sucursal_codigo: str, owner_email: str, canal: str = ""):
    _get_conn().execute(
        "INSERT OR REPLACE INTO ownership (lead_id, sucursal_codigo, owner_email, fecha_toma, canal) VALUES (?,?,?,?,?)",
        (lead_id, sucursal_codigo, owner_email, datetime.now().isoformat(), canal),
    )
    _get_conn().commit()


def obtener_owner(lead_id: str, sucursal_codigo: str) -> dict | None:
    row = _get_conn().execute(
        "SELECT o.*, u.nombre, u.apellido, u.color FROM ownership o JOIN usuarios u ON o.owner_email = u.email WHERE o.lead_id = ? AND o.sucursal_codigo = ?",
        (lead_id, sucursal_codigo),
    ).fetchone()
    return dict(row) if row else None


def listar_ownership_sucursal(sucursal_codigo: str) -> dict:
    """Retorna {lead_id: {owner_email, nombre, apellido, color, fecha_toma}}."""
    rows = _get_conn().execute(
        "SELECT o.lead_id, o.owner_email, o.fecha_toma, u.nombre, u.apellido, u.color FROM ownership o JOIN usuarios u ON o.owner_email = u.email WHERE o.sucursal_codigo = ?",
        (sucursal_codigo,),
    ).fetchall()
    return {r["lead_id"]: dict(r) for r in rows}


def reasignar_ownership(lead_id: str, sucursal_codigo: str, nuevo_email: str):
    _get_conn().execute(
        "UPDATE ownership SET owner_email = ?, fecha_toma = ? WHERE lead_id = ? AND sucursal_codigo = ?",
        (nuevo_email, datetime.now().isoformat(), lead_id, sucursal_codigo),
    )
    _get_conn().commit()


def eliminar_ownership(lead_id: str, sucursal_codigo: str):
    _get_conn().execute("DELETE FROM ownership WHERE lead_id = ? AND sucursal_codigo = ?", (lead_id, sucursal_codigo))
    _get_conn().commit()


# ── Cartera ──────────────────────────────────────────────────────────────────

def guardar_cliente_cartera(owner_email: str, datos: dict) -> int:
    ahora = datetime.now().isoformat()
    cur = _get_conn().execute(
        """INSERT INTO cartera (owner_email, nombre_razon_social, cuit, rubro, subrubro, telefono, mail, direccion, localidad, observaciones, nivel_paquete, criterios_json, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            owner_email,
            datos.get("nombre_razon_social", ""),
            datos.get("cuit", ""),
            datos.get("rubro", ""),
            datos.get("subrubro", ""),
            datos.get("telefono", ""),
            datos.get("mail", ""),
            datos.get("direccion", ""),
            datos.get("localidad", ""),
            datos.get("observaciones", ""),
            datos.get("nivel_paquete", ""),
            datos.get("criterios_json", "{}"),
            ahora, ahora,
        ),
    )
    _get_conn().commit()
    return cur.lastrowid


def listar_cartera(owner_email: str) -> list[dict]:
    rows = _get_conn().execute("SELECT * FROM cartera WHERE owner_email = ? ORDER BY updated_at DESC", (owner_email,)).fetchall()
    return [dict(r) for r in rows]


def listar_cartera_todos() -> list[dict]:
    rows = _get_conn().execute(
        "SELECT c.*, u.nombre as owner_nombre, u.apellido as owner_apellido, u.color as owner_color FROM cartera c JOIN usuarios u ON c.owner_email = u.email ORDER BY c.updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def actualizar_cliente_cartera(id_cliente: int, datos: dict) -> bool:
    permitidos = {"nombre_razon_social", "cuit", "rubro", "subrubro", "telefono", "mail", "direccion", "localidad", "observaciones", "nivel_paquete", "criterios_json"}
    campos = {k: v for k, v in datos.items() if k in permitidos}
    if not campos:
        return False
    campos["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k} = ?" for k in campos)
    vals = list(campos.values()) + [id_cliente]
    _get_conn().execute(f"UPDATE cartera SET {sets} WHERE id = ?", vals)
    _get_conn().commit()
    return True


def eliminar_cliente_cartera(id_cliente: int):
    _get_conn().execute("DELETE FROM cartera WHERE id = ?", (id_cliente,))
    _get_conn().commit()


def importar_cartera_excel(owner_email: str, df) -> int:
    """Importa DataFrame a la cartera del usuario (agrega). Retorna cantidad insertada."""
    import pandas as pd
    count = 0
    for _, row in df.iterrows():
        datos = _mapear_fila_cartera(row, df.columns)
        if datos.get("nombre_razon_social"):
            guardar_cliente_cartera(owner_email, datos)
            count += 1
    return count


# Criterios comerciales del informe roles (columnas reales del banco)
CRITERIOS_COMERCIALES = {
    "acreditacion_cupon": "Acreditación Cupón",
    "art_y_seguros": "ART y Seguros",
    "desc_cheques": "Descuento Cheques",
    "haberes": "Haberes",
    "cdni_comercio": "CDNI Comercio",
    "comex": "Comex",
    "echeq": "Emisión/Dep. Echeq",
    "emp_proveedora": "Emp. Proveedora",
    "garantias_on": "Garantías ON",
    "inversion_financiera": "Inversión Financiera",
    "pactar": "Pactar",
    "prestamos_inversion": "Préstamos Inversión",
}


def _mapear_fila_cartera(row, columnas) -> dict:
    """Mapea una fila de Excel a campos de cartera con auto-detección de columnas."""
    import pandas as pd
    col_map = {}
    criterios = {}

    for c in columnas:
        cl = str(c).strip().lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        # Campos base
        if cl in ("nombre", "razon_social", "razón_social", "nombre_razon_social", "empresa", "comercio", "cliente", "denominacion"):
            col_map["nombre_razon_social"] = c
        elif cl in ("cuit", "cuit/cuil", "cuil", "cuit_cuil"):
            col_map["cuit"] = c
        elif cl in ("rubro", "actividad", "categoria", "actividad_principal"):
            col_map["rubro"] = c
        elif cl in ("subrubro", "sub_rubro"):
            col_map["subrubro"] = c
        elif cl in ("telefono", "teléfono", "tel", "celular"):
            col_map["telefono"] = c
        elif cl in ("mail", "email", "correo"):
            col_map["mail"] = c
        elif cl in ("direccion", "dirección", "domicilio"):
            col_map["direccion"] = c
        elif cl in ("localidad", "ciudad", "partido"):
            col_map["localidad"] = c
        elif cl in ("observaciones", "notas", "comentarios"):
            col_map["observaciones"] = c
        elif cl in ("paquete", "nivel", "nivel_paquete", "modulo", "tipo_paquete", "categoria_paquete"):
            col_map["nivel_paquete"] = c
        # Criterios comerciales
        elif "saldo" in cl and ("promedio" in cl or "prom" in cl):
            criterios["saldo_promedio"] = c
        elif "transferencia" in cl or "transf" in cl:
            criterios["transferencias"] = c
        elif "consumo" in cl or "tarjeta" in cl:
            criterios["consumos_tc"] = c
        elif "inversion" in cl or "inversión" in cl:
            criterios["inversiones"] = c
        elif "cupon" in cl or "cobro" in cl or "cupón" in cl:
            criterios["cupones_cobros"] = c
        elif "seguro" in cl:
            criterios["seguros"] = c
        elif "nomina" in cl or "empleado" in cl or "nómina" in cl:
            criterios["nomina"] = c
        elif "debito" in cl or "débito" in cl:
            criterios["debitos_auto"] = c
        elif "haber" in cl or "sueldo" in cl:
            criterios["haberes"] = c

    datos = {}
    for campo_interno, col_excel in col_map.items():
        val = row.get(col_excel, "")
        datos[campo_interno] = "" if pd.isna(val) else str(val).strip()

    # Extraer criterios como booleans
    criterios_dict = {}
    for crit_id, col_excel in criterios.items():
        val = row.get(col_excel, "")
        if pd.isna(val) or str(val).strip() == "":
            criterios_dict[crit_id] = False
        else:
            sv = str(val).strip().lower()
            criterios_dict[crit_id] = sv in ("si", "sí", "s", "1", "true", "x", "cumple", "ok", "✓", "✔")
            # Si es numérico > 0, también es True
            if not criterios_dict[crit_id]:
                try:
                    criterios_dict[crit_id] = float(val) > 0
                except (ValueError, TypeError):
                    pass
    if criterios_dict:
        import json
        datos["criterios_json"] = json.dumps(criterios_dict, ensure_ascii=False)

    return datos


def importar_informe_roles(owner_email: str, archivo, codigo_afiliado: str) -> dict:
    """
    Importa informe roles (.xlsb): lee INFO_CARTERA, filtra por afiliado,
    REEMPLAZA toda la cartera del usuario. Retorna reporte de cambios.
    """
    import pandas as pd
    import json

    # Leer hoja INFO_CARTERA del .xlsb
    try:
        df = pd.read_excel(archivo, sheet_name="INFO_CARTERA", header=None, dtype=str, engine="pyxlsb")
    except Exception:
        # Fallback: intentar como xlsx normal
        df = pd.read_excel(archivo, sheet_name=0, header=None, dtype=str)

    # Encontrar fila de encabezados (buscar "CUIT")
    header_row = None
    for i, row in df.iterrows():
        for v in row:
            if str(v).strip().upper() == "CUIT":
                header_row = i
                break
        if header_row is not None:
            break

    if header_row is None:
        return {"importados": 0, "error": "No se encontró encabezado con CUIT"}

    # Rearmar DataFrame con encabezados correctos
    df.columns = [str(v).strip() if str(v) != "nan" else f"col_{j}" for j, v in enumerate(df.iloc[header_row])]
    df = df.iloc[header_row + 1:].reset_index(drop=True)

    # Filtrar por afiliado del usuario
    col_afiliado = None
    for c in df.columns:
        if "afiliado" in c.lower():
            col_afiliado = c
            break
    if col_afiliado and codigo_afiliado:
        df = df[df[col_afiliado].str.strip().str.upper() == codigo_afiliado.strip().upper()]

    if df.empty:
        return {"importados": 0, "clientes_nuevos": [], "clientes_perdidos": [], "cambios_criterios": [],
                "error": f"No se encontraron clientes para afiliado {codigo_afiliado}"}

    # Mapeo de columnas del informe a campos de cartera
    _col_map = {}
    _crit_map = {}
    for c in df.columns:
        cl = str(c).strip().upper()
        if cl == "TITULAR":
            _col_map["nombre_razon_social"] = c
        elif cl == "CUIT":
            _col_map["cuit"] = c
        elif "ACTIVIDAD" in cl or "DESC_ACTIVIDAD" in cl:
            _col_map["rubro"] = c
        elif cl == "RECIPROCIDAD":
            _col_map["subrubro"] = c  # guardar reciprocidad en subrubro
        elif cl == "GESTIONADO":
            _col_map["observaciones_gestionado"] = c
        # Criterios
        elif "ACREDITACION_CUPON" in cl or "ACREDITACION CUPON" in cl:
            _crit_map["acreditacion_cupon"] = c
        elif "ART" in cl and "SEGURO" in cl:
            _crit_map["art_y_seguros"] = c
        elif "DESC_CHEQUE" in cl or "DESC CHEQUE" in cl:
            _crit_map["desc_cheques"] = c
        elif "HABER" in cl:
            _crit_map["haberes"] = c
        elif "CDNI" in cl:
            _crit_map["cdni_comercio"] = c
        elif cl == "COMEX" or "COMEX" in cl:
            _crit_map["comex"] = c
        elif "ECHEQ" in cl:
            _crit_map["echeq"] = c
        elif "PROVEDORA" in cl or "PROVEEDORA" in cl:
            _crit_map["emp_proveedora"] = c
        elif "GARANTIA" in cl:
            _crit_map["garantias_on"] = c
        elif "INVERSION_FINANCIERA" in cl or "INVERSION FINANCIERA" in cl:
            _crit_map["inversion_financiera"] = c
        elif cl == "PACTAR" or "PACTAR" in cl:
            _crit_map["pactar"] = c
        elif "PRESTAMO" in cl and "INVERSION" in cl:
            _crit_map["prestamos_inversion"] = c

    # Snapshot anterior por CUIT
    anteriores = listar_cartera(owner_email)
    ant_por_cuit = {}
    for c in anteriores:
        cuit = c.get("cuit", "").strip()
        if cuit:
            ant_por_cuit[cuit] = c

    # Borrar cartera actual
    _get_conn().execute("DELETE FROM cartera WHERE owner_email = ?", (owner_email,))
    _get_conn().commit()

    # Importar nuevos
    nuevos_por_cuit = {}
    count = 0
    for _, row in df.iterrows():
        nombre = str(row.get(_col_map.get("nombre_razon_social", ""), "")).strip()
        if not nombre or nombre in ("nan", "None", "?"):
            continue
        cuit = str(row.get(_col_map.get("cuit", ""), "")).strip()
        rubro = str(row.get(_col_map.get("rubro", ""), "")).strip()
        reciprocidad = str(row.get(_col_map.get("subrubro", ""), "")).strip()

        # Criterios: interpretar 0 como False, >0 como True
        criterios = {}
        for crit_id, col in _crit_map.items():
            val = row.get(col, "0")
            try:
                criterios[crit_id] = int(float(str(val))) > 0
            except (ValueError, TypeError):
                criterios[crit_id] = False

        datos = {
            "nombre_razon_social": nombre if nombre != "nan" else "",
            "cuit": cuit if cuit != "nan" else "",
            "rubro": rubro if rubro != "nan" else "",
            "subrubro": reciprocidad if reciprocidad != "nan" else "",
            "criterios_json": json.dumps(criterios, ensure_ascii=False),
        }
        guardar_cliente_cartera(owner_email, datos)
        if cuit and cuit != "nan":
            nuevos_por_cuit[cuit] = datos
        count += 1

    # Generar diff
    cuits_ant = set(ant_por_cuit.keys())
    cuits_new = set(nuevos_por_cuit.keys())
    clientes_nuevos = cuits_new - cuits_ant
    clientes_perdidos = cuits_ant - cuits_new
    clientes_mantienen = cuits_ant & cuits_new

    cambios_criterios = []
    for cuit in clientes_mantienen:
        ant = ant_por_cuit[cuit]
        nuevo = nuevos_por_cuit[cuit]
        nombre = nuevo.get("nombre_razon_social", ant.get("nombre_razon_social", ""))
        try:
            crit_ant = json.loads(ant.get("criterios_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            crit_ant = {}
        try:
            crit_new = json.loads(nuevo.get("criterios_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            crit_new = {}

        subieron = [k for k in crit_new if crit_new.get(k) and not crit_ant.get(k)]
        bajaron = [k for k in crit_ant if crit_ant.get(k) and not crit_new.get(k)]
        if subieron or bajaron:
            cambios_criterios.append({
                "cuit": cuit, "nombre": nombre,
                "subieron": subieron, "bajaron": bajaron,
            })

    return {
        "importados": count,
        "clientes_nuevos": [nuevos_por_cuit[c].get("nombre_razon_social", c) for c in clientes_nuevos],
        "clientes_perdidos": [ant_por_cuit[c].get("nombre_razon_social", c) for c in clientes_perdidos],
        "cambios_criterios": cambios_criterios,
    }
