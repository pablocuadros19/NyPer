"""
Base de datos SQLite — memoria persistente del jugador.
"""

import sqlite3
import os
import json
from datetime import datetime

from config import DB_PATH


def _conectar():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def inicializar_db():
    """Crea las tablas si no existen."""
    conn = _conectar()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS jugador (
            id INTEGER PRIMARY KEY,
            nombre TEXT NOT NULL,
            edad INTEGER,
            nombre_profesor TEXT DEFAULT 'Profe',
            nivel INTEGER DEFAULT 1,
            fecha_creacion DATE DEFAULT (date('now')),
            total_partidas INTEGER DEFAULT 0,
            total_victorias INTEGER DEFAULT 0,
            color_preferido TEXT DEFAULT 'blancas',
            modo_ensenanza INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY,
            jugador_id INTEGER,
            fecha TIMESTAMP DEFAULT (datetime('now')),
            duracion_minutos INTEGER,
            resultado TEXT,
            movimientos TEXT,
            nivel_oponente INTEGER,
            notas_profesor TEXT,
            FOREIGN KEY (jugador_id) REFERENCES jugador(id)
        );

        CREATE TABLE IF NOT EXISTS conceptos (
            id INTEGER PRIMARY KEY,
            jugador_id INTEGER,
            concepto TEXT,
            estado TEXT DEFAULT 'introducido',
            ultima_practica DATE,
            veces_practicado INTEGER DEFAULT 0,
            notas TEXT,
            FOREIGN KEY (jugador_id) REFERENCES jugador(id)
        );

        CREATE TABLE IF NOT EXISTS errores_frecuentes (
            id INTEGER PRIMARY KEY,
            jugador_id INTEGER,
            descripcion TEXT,
            frecuencia INTEGER DEFAULT 1,
            ultima_vez DATE,
            superado INTEGER DEFAULT 0,
            FOREIGN KEY (jugador_id) REFERENCES jugador(id)
        );

        CREATE TABLE IF NOT EXISTS sesiones (
            id INTEGER PRIMARY KEY,
            jugador_id INTEGER,
            fecha TIMESTAMP DEFAULT (datetime('now')),
            resumen TEXT,
            conceptos_trabajados TEXT,
            estado_animo TEXT,
            FOREIGN KEY (jugador_id) REFERENCES jugador(id)
        );
    """)
    conn.commit()
    conn.close()


# --- Jugador ---

def crear_jugador(nombre, edad, nombre_profesor="El Profe", nivel_inicial=1):
    conn = _conectar()
    cursor = conn.execute(
        "INSERT INTO jugador (nombre, edad, nombre_profesor, nivel) VALUES (?, ?, ?, ?)",
        (nombre, edad, nombre_profesor, nivel_inicial)
    )
    jugador_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jugador_id


def obtener_jugador(jugador_id=None):
    """Obtiene el jugador. Si no se pasa id, devuelve el primero (uso single-player)."""
    conn = _conectar()
    if jugador_id:
        row = conn.execute("SELECT * FROM jugador WHERE id = ?", (jugador_id,)).fetchone()
    else:
        row = conn.execute("SELECT * FROM jugador ORDER BY id LIMIT 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def actualizar_jugador(jugador_id, **campos):
    conn = _conectar()
    sets = ", ".join(f"{k} = ?" for k in campos)
    valores = list(campos.values()) + [jugador_id]
    conn.execute(f"UPDATE jugador SET {sets} WHERE id = ?", valores)
    conn.commit()
    conn.close()


def incrementar_partidas(jugador_id, victoria=False):
    conn = _conectar()
    conn.execute("UPDATE jugador SET total_partidas = total_partidas + 1 WHERE id = ?", (jugador_id,))
    if victoria:
        conn.execute("UPDATE jugador SET total_victorias = total_victorias + 1 WHERE id = ?", (jugador_id,))
    conn.commit()
    conn.close()


# --- Partidas ---

def guardar_partida(jugador_id, resultado, movimientos_pgn, nivel_oponente, duracion=None, notas=None):
    conn = _conectar()
    conn.execute(
        "INSERT INTO partidas (jugador_id, resultado, movimientos, nivel_oponente, duracion_minutos, notas_profesor) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (jugador_id, resultado, movimientos_pgn, nivel_oponente, duracion, notas)
    )
    conn.commit()
    conn.close()


def obtener_ultimas_partidas(jugador_id, limite=5):
    conn = _conectar()
    rows = conn.execute(
        "SELECT * FROM partidas WHERE jugador_id = ? ORDER BY fecha DESC LIMIT ?",
        (jugador_id, limite)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Conceptos ---

def registrar_concepto(jugador_id, concepto, estado="introducido"):
    conn = _conectar()
    existente = conn.execute(
        "SELECT id FROM conceptos WHERE jugador_id = ? AND concepto = ?",
        (jugador_id, concepto)
    ).fetchone()
    if existente:
        conn.execute(
            "UPDATE conceptos SET estado = ?, ultima_practica = date('now'), "
            "veces_practicado = veces_practicado + 1 WHERE id = ?",
            (estado, existente["id"])
        )
    else:
        conn.execute(
            "INSERT INTO conceptos (jugador_id, concepto, estado, ultima_practica) "
            "VALUES (?, ?, ?, date('now'))",
            (jugador_id, concepto, estado)
        )
    conn.commit()
    conn.close()


def obtener_conceptos(jugador_id):
    conn = _conectar()
    rows = conn.execute(
        "SELECT * FROM conceptos WHERE jugador_id = ? ORDER BY ultima_practica DESC",
        (jugador_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Errores ---

def registrar_error(jugador_id, descripcion):
    conn = _conectar()
    existente = conn.execute(
        "SELECT id, frecuencia FROM errores_frecuentes WHERE jugador_id = ? AND descripcion = ?",
        (jugador_id, descripcion)
    ).fetchone()
    if existente:
        conn.execute(
            "UPDATE errores_frecuentes SET frecuencia = ?, ultima_vez = date('now') WHERE id = ?",
            (existente["frecuencia"] + 1, existente["id"])
        )
    else:
        conn.execute(
            "INSERT INTO errores_frecuentes (jugador_id, descripcion, ultima_vez) VALUES (?, ?, date('now'))",
            (jugador_id, descripcion)
        )
    conn.commit()
    conn.close()


def obtener_errores(jugador_id, solo_activos=True):
    conn = _conectar()
    query = "SELECT * FROM errores_frecuentes WHERE jugador_id = ?"
    if solo_activos:
        query += " AND superado = 0"
    query += " ORDER BY frecuencia DESC"
    rows = conn.execute(query, (jugador_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --- Sesiones ---

def guardar_sesion(jugador_id, resumen, conceptos_trabajados=None, estado_animo=None):
    conn = _conectar()
    conn.execute(
        "INSERT INTO sesiones (jugador_id, resumen, conceptos_trabajados, estado_animo) "
        "VALUES (?, ?, ?, ?)",
        (jugador_id, resumen, conceptos_trabajados, estado_animo)
    )
    conn.commit()
    conn.close()


def obtener_ultimas_sesiones(jugador_id, limite=5):
    conn = _conectar()
    rows = conn.execute(
        "SELECT * FROM sesiones WHERE jugador_id = ? ORDER BY fecha DESC LIMIT ?",
        (jugador_id, limite)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def armar_contexto_profesor(jugador_id):
    """Arma un resumen completo para el system prompt del profesor."""
    jugador = obtener_jugador(jugador_id)
    if not jugador:
        return None

    sesiones = obtener_ultimas_sesiones(jugador_id, 3)
    conceptos = obtener_conceptos(jugador_id)
    errores = obtener_errores(jugador_id)
    partidas = obtener_ultimas_partidas(jugador_id, 3)

    dominados = [c["concepto"] for c in conceptos if c["estado"] == "dominado"]
    en_progreso = [c["concepto"] for c in conceptos if c["estado"] == "en_progreso"]
    errores_activos = [f"{e['descripcion']} (x{e['frecuencia']})" for e in errores[:5]]

    resumen_sesiones = ""
    for s in sesiones:
        resumen_sesiones += f"- {s['fecha'][:10]}: {s['resumen']}\n"

    return {
        "nombre": jugador["nombre"],
        "edad": jugador["edad"],
        "nombre_profesor": jugador["nombre_profesor"],
        "nivel": jugador["nivel"],
        "total_partidas": jugador["total_partidas"],
        "total_victorias": jugador["total_victorias"],
        "puntos_fuertes": ", ".join(dominados) if dominados else "todavía explorando",
        "puntos_a_mejorar": ", ".join(errores_activos) if errores_activos else "recién empieza",
        "jugadas_dominadas": ", ".join(dominados) if dominados else "ninguna todavía",
        "jugadas_en_progreso": ", ".join(en_progreso) if en_progreso else "ninguna todavía",
        "resumen_ultimas_sesiones": resumen_sesiones if resumen_sesiones else "primera sesión",
        "modo_ensenanza": jugador["modo_ensenanza"],
    }
