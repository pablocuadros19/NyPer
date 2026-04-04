"""
Base de datos para NyPer.
Backend primario: Supabase (persiste en la nube).
Fallback: SQLite local (para desarrollo sin Supabase).
Tablas: usuarios, ownership, cartera.
"""

import os
import json
import sqlite3
from datetime import datetime

import streamlit as st

_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "nyper.db")
_ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "pablo.cuadros@bpba.com.ar")


# ── Backend detection ───────────────────────────────────────────────────────

try:
    from supabase import create_client
except ImportError:
    create_client = None


@st.cache_resource
def _get_supabase():
    if create_client is None:
        return None
    url = ""
    key = ""
    try:
        url = st.secrets.get("SUPABASE_URL", "") or os.getenv("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "") or os.getenv("SUPABASE_KEY", "")
    except Exception:
        url = os.getenv("SUPABASE_URL", "")
        key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception:
        return None


def _usa_supabase() -> bool:
    return _get_supabase() is not None


@st.cache_resource
def _get_sqlite():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ── Inicialización ──────────────────────────────────────────────────────────

def inicializar_db():
    """Crea tablas e inserta admin seed."""
    if _usa_supabase():
        _inicializar_supabase()
    else:
        _inicializar_sqlite()


def _inicializar_supabase():
    sb = _get_supabase()
    # Las tablas se crean con el SQL script, solo verificar admin seed
    try:
        result = sb.table("usuarios").select("email").eq("email", _ADMIN_EMAIL).execute()
        if not result.data:
            from services.auth import _hash_password, _generar_salt
            salt = _generar_salt()
            pw_hash = _hash_password("nyper2026", salt)
            sb.table("usuarios").insert({
                "email": _ADMIN_EMAIL, "nombre": "Pablo", "apellido": "Cuadros",
                "password_hash": pw_hash, "salt": salt, "rol": "admin",
                "color": "#00A651", "activo": 1, "codigo_afiliado": "",
                "created_at": datetime.now().isoformat(),
            }).execute()
    except Exception:
        pass


def _inicializar_sqlite():
    conn = _get_sqlite()
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
    # Migraciones
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


# ══════════════════════════════════════════════════════════════════════════════
# USUARIOS
# ══════════════════════════════════════════════════════════════════════════════

def obtener_usuario(email: str) -> dict | None:
    if _usa_supabase():
        try:
            r = _get_supabase().table("usuarios").select("*").eq("email", email).execute()
            return r.data[0] if r.data else None
        except Exception:
            pass
    row = _get_sqlite().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def crear_usuario(email: str, nombre: str, apellido: str, password: str, rol: str = "usuario", color: str = "#3b82f6") -> bool:
    from services.auth import _hash_password, _generar_salt
    salt = _generar_salt()
    pw_hash = _hash_password(password, salt)
    data = {
        "email": email, "nombre": nombre, "apellido": apellido,
        "password_hash": pw_hash, "salt": salt, "rol": rol,
        "color": color, "activo": 1, "codigo_afiliado": "",
        "created_at": datetime.now().isoformat(),
    }
    if _usa_supabase():
        try:
            _get_supabase().table("usuarios").insert(data).execute()
            return True
        except Exception:
            return False
    try:
        _get_sqlite().execute(
            "INSERT INTO usuarios (email, nombre, apellido, password_hash, salt, rol, color, activo, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (email, nombre, apellido, pw_hash, salt, rol, color, 1, data["created_at"]),
        )
        _get_sqlite().commit()
        return True
    except sqlite3.IntegrityError:
        return False


def listar_usuarios() -> list[dict]:
    if _usa_supabase():
        try:
            r = _get_supabase().table("usuarios").select("email, nombre, apellido, rol, color, activo, codigo_afiliado, created_at, last_login").order("nombre").execute()
            return r.data or []
        except Exception:
            pass
    rows = _get_sqlite().execute("SELECT email, nombre, apellido, rol, color, activo, codigo_afiliado, created_at, last_login FROM usuarios ORDER BY nombre").fetchall()
    return [dict(r) for r in rows]


def actualizar_usuario(email: str, **campos) -> bool:
    permitidos = {"nombre", "apellido", "rol", "color", "activo", "last_login", "codigo_afiliado"}
    campos_filtrados = {k: v for k, v in campos.items() if k in permitidos}
    if not campos_filtrados:
        return False
    if _usa_supabase():
        try:
            _get_supabase().table("usuarios").update(campos_filtrados).eq("email", email).execute()
            return True
        except Exception:
            pass
    sets = ", ".join(f"{k} = ?" for k in campos_filtrados)
    vals = list(campos_filtrados.values()) + [email]
    _get_sqlite().execute(f"UPDATE usuarios SET {sets} WHERE email = ?", vals)
    _get_sqlite().commit()
    return True


def cambiar_password(email: str, nueva_password: str) -> bool:
    from services.auth import _hash_password, _generar_salt
    salt = _generar_salt()
    pw_hash = _hash_password(nueva_password, salt)
    if _usa_supabase():
        try:
            _get_supabase().table("usuarios").update({"password_hash": pw_hash, "salt": salt}).eq("email", email).execute()
            return True
        except Exception:
            pass
    _get_sqlite().execute("UPDATE usuarios SET password_hash = ?, salt = ? WHERE email = ?", (pw_hash, salt, email))
    _get_sqlite().commit()
    return True


# ══════════════════════════════════════════════════════════════════════════════
# OWNERSHIP
# ══════════════════════════════════════════════════════════════════════════════

def registrar_ownership(lead_id: str, sucursal_codigo: str, owner_email: str, canal: str = ""):
    data = {
        "lead_id": lead_id, "sucursal_codigo": sucursal_codigo,
        "owner_email": owner_email, "fecha_toma": datetime.now().isoformat(),
        "canal": canal,
    }
    if _usa_supabase():
        try:
            _get_supabase().table("ownership").upsert(data).execute()
            return
        except Exception:
            pass
    _get_sqlite().execute(
        "INSERT OR REPLACE INTO ownership (lead_id, sucursal_codigo, owner_email, fecha_toma, canal) VALUES (?,?,?,?,?)",
        (data["lead_id"], data["sucursal_codigo"], data["owner_email"], data["fecha_toma"], data["canal"]),
    )
    _get_sqlite().commit()


def obtener_owner(lead_id: str, sucursal_codigo: str) -> dict | None:
    if _usa_supabase():
        try:
            sb = _get_supabase()
            r = sb.table("ownership").select("*").eq("lead_id", lead_id).eq("sucursal_codigo", sucursal_codigo).execute()
            if r.data:
                o = r.data[0]
                u = sb.table("usuarios").select("nombre, apellido, color").eq("email", o["owner_email"]).execute()
                if u.data:
                    o.update(u.data[0])
                return o
        except Exception:
            pass
    row = _get_sqlite().execute(
        "SELECT o.*, u.nombre, u.apellido, u.color FROM ownership o JOIN usuarios u ON o.owner_email = u.email WHERE o.lead_id = ? AND o.sucursal_codigo = ?",
        (lead_id, sucursal_codigo),
    ).fetchone()
    return dict(row) if row else None


def listar_ownership_sucursal(sucursal_codigo: str) -> dict:
    """Retorna {lead_id: {owner_email, nombre, apellido, color, fecha_toma}}."""
    if _usa_supabase():
        try:
            sb = _get_supabase()
            r = sb.table("ownership").select("*").eq("sucursal_codigo", sucursal_codigo).execute()
            result = {}
            if r.data:
                emails = list(set(o["owner_email"] for o in r.data))
                u_r = sb.table("usuarios").select("email, nombre, apellido, color").in_("email", emails).execute()
                u_map = {u["email"]: u for u in (u_r.data or [])}
                for o in r.data:
                    o.update(u_map.get(o["owner_email"], {}))
                    result[o["lead_id"]] = o
            return result
        except Exception:
            pass
    rows = _get_sqlite().execute(
        "SELECT o.lead_id, o.owner_email, o.fecha_toma, u.nombre, u.apellido, u.color FROM ownership o JOIN usuarios u ON o.owner_email = u.email WHERE o.sucursal_codigo = ?",
        (sucursal_codigo,),
    ).fetchall()
    return {r["lead_id"]: dict(r) for r in rows}


def reasignar_ownership(lead_id: str, sucursal_codigo: str, nuevo_email: str):
    ahora = datetime.now().isoformat()
    if _usa_supabase():
        try:
            _get_supabase().table("ownership").update(
                {"owner_email": nuevo_email, "fecha_toma": ahora}
            ).eq("lead_id", lead_id).eq("sucursal_codigo", sucursal_codigo).execute()
            return
        except Exception:
            pass
    _get_sqlite().execute(
        "UPDATE ownership SET owner_email = ?, fecha_toma = ? WHERE lead_id = ? AND sucursal_codigo = ?",
        (nuevo_email, ahora, lead_id, sucursal_codigo),
    )
    _get_sqlite().commit()


def eliminar_ownership(lead_id: str, sucursal_codigo: str):
    if _usa_supabase():
        try:
            _get_supabase().table("ownership").delete().eq("lead_id", lead_id).eq("sucursal_codigo", sucursal_codigo).execute()
            return
        except Exception:
            pass
    _get_sqlite().execute("DELETE FROM ownership WHERE lead_id = ? AND sucursal_codigo = ?", (lead_id, sucursal_codigo))
    _get_sqlite().commit()


# ══════════════════════════════════════════════════════════════════════════════
# CARTERA
# ══════════════════════════════════════════════════════════════════════════════

def guardar_cliente_cartera(owner_email: str, datos: dict) -> int:
    ahora = datetime.now().isoformat()
    data = {
        "owner_email": owner_email,
        "nombre_razon_social": datos.get("nombre_razon_social", ""),
        "cuit": datos.get("cuit", ""),
        "rubro": datos.get("rubro", ""),
        "subrubro": datos.get("subrubro", ""),
        "telefono": datos.get("telefono", ""),
        "mail": datos.get("mail", ""),
        "direccion": datos.get("direccion", ""),
        "localidad": datos.get("localidad", ""),
        "observaciones": datos.get("observaciones", ""),
        "nivel_paquete": datos.get("nivel_paquete", ""),
        "criterios_json": datos.get("criterios_json", "{}"),
        "created_at": ahora, "updated_at": ahora,
    }
    if _usa_supabase():
        try:
            r = _get_supabase().table("cartera").insert(data).execute()
            return r.data[0]["id"] if r.data else 0
        except Exception:
            pass
    cur = _get_sqlite().execute(
        """INSERT INTO cartera (owner_email, nombre_razon_social, cuit, rubro, subrubro, telefono, mail, direccion, localidad, observaciones, nivel_paquete, criterios_json, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (data["owner_email"], data["nombre_razon_social"], data["cuit"], data["rubro"],
         data["subrubro"], data["telefono"], data["mail"], data["direccion"],
         data["localidad"], data["observaciones"], data["nivel_paquete"],
         data["criterios_json"], ahora, ahora),
    )
    _get_sqlite().commit()
    return cur.lastrowid


def listar_cartera(owner_email: str) -> list[dict]:
    if _usa_supabase():
        try:
            r = _get_supabase().table("cartera").select("*").eq("owner_email", owner_email).order("updated_at", desc=True).execute()
            return r.data or []
        except Exception:
            pass
    rows = _get_sqlite().execute("SELECT * FROM cartera WHERE owner_email = ? ORDER BY updated_at DESC", (owner_email,)).fetchall()
    return [dict(r) for r in rows]


def listar_cartera_todos() -> list[dict]:
    if _usa_supabase():
        try:
            sb = _get_supabase()
            r = sb.table("cartera").select("*").order("updated_at", desc=True).execute()
            if r.data:
                emails = list(set(c["owner_email"] for c in r.data))
                u_r = sb.table("usuarios").select("email, nombre, apellido, color").in_("email", emails).execute()
                u_map = {u["email"]: u for u in (u_r.data or [])}
                for c in r.data:
                    u = u_map.get(c["owner_email"], {})
                    c["owner_nombre"] = u.get("nombre", "")
                    c["owner_apellido"] = u.get("apellido", "")
                    c["owner_color"] = u.get("color", "#3b82f6")
            return r.data or []
        except Exception:
            pass
    rows = _get_sqlite().execute(
        "SELECT c.*, u.nombre as owner_nombre, u.apellido as owner_apellido, u.color as owner_color FROM cartera c JOIN usuarios u ON c.owner_email = u.email ORDER BY c.updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def actualizar_cliente_cartera(id_cliente: int, datos: dict) -> bool:
    permitidos = {"nombre_razon_social", "cuit", "rubro", "subrubro", "telefono", "mail", "direccion", "localidad", "observaciones", "nivel_paquete", "criterios_json"}
    campos = {k: v for k, v in datos.items() if k in permitidos}
    if not campos:
        return False
    campos["updated_at"] = datetime.now().isoformat()
    if _usa_supabase():
        try:
            _get_supabase().table("cartera").update(campos).eq("id", id_cliente).execute()
            return True
        except Exception:
            pass
    sets = ", ".join(f"{k} = ?" for k in campos)
    vals = list(campos.values()) + [id_cliente]
    _get_sqlite().execute(f"UPDATE cartera SET {sets} WHERE id = ?", vals)
    _get_sqlite().commit()
    return True


def eliminar_cliente_cartera(id_cliente: int):
    if _usa_supabase():
        try:
            _get_supabase().table("cartera").delete().eq("id", id_cliente).execute()
            return
        except Exception:
            pass
    _get_sqlite().execute("DELETE FROM cartera WHERE id = ?", (id_cliente,))
    _get_sqlite().commit()


def importar_cartera_excel(owner_email: str, df) -> int:
    """Importa DataFrame a la cartera del usuario (agrega)."""
    count = 0
    for _, row in df.iterrows():
        datos = _mapear_fila_cartera(row, df.columns)
        if datos.get("nombre_razon_social"):
            guardar_cliente_cartera(owner_email, datos)
            count += 1
    return count


# ── Criterios comerciales del informe roles ─────────────────────────────────

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

    for c in columnas:
        cl = str(c).strip().lower().replace(" ", "_").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
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

    datos = {}
    for campo_interno, col_excel in col_map.items():
        val = row.get(col_excel, "")
        datos[campo_interno] = "" if pd.isna(val) else str(val).strip()

    return datos


def importar_informe_roles(owner_email: str, archivo, codigo_afiliado: str) -> dict:
    """
    Importa informe roles (.xlsb): lee INFO_CARTERA, filtra por afiliado,
    REEMPLAZA toda la cartera del usuario. Retorna reporte de cambios.
    """
    import pandas as pd

    try:
        df = pd.read_excel(archivo, sheet_name="INFO_CARTERA", header=None, dtype=str, engine="pyxlsb")
    except Exception:
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

    df.columns = [str(v).strip() if str(v) != "nan" else f"col_{j}" for j, v in enumerate(df.iloc[header_row])]
    df = df.iloc[header_row + 1:].reset_index(drop=True)

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
            _col_map["subrubro"] = c
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

    # Snapshot anterior
    anteriores = listar_cartera(owner_email)
    ant_por_cuit = {}
    for c in anteriores:
        cuit = c.get("cuit", "").strip()
        if cuit:
            ant_por_cuit[cuit] = c

    # Borrar cartera actual
    if _usa_supabase():
        try:
            _get_supabase().table("cartera").delete().eq("owner_email", owner_email).execute()
        except Exception:
            pass
    else:
        _get_sqlite().execute("DELETE FROM cartera WHERE owner_email = ?", (owner_email,))
        _get_sqlite().commit()

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

    # Diff
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
