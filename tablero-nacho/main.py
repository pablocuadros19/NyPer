"""
Tablero Nacho — Ajedrez con IA Profesor
Entry point de la aplicación.
"""

import sys
import os

# Agregar directorio del proyecto al path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify, session
from datetime import datetime

from config import PUERTO_WEB, NIVELES_OPONENTE
from motor.ajedrez import TableroAjedrez
from oponente.ia_oponente import OponenteIA
from memoria.database import (
    inicializar_db, crear_jugador, obtener_jugador, actualizar_jugador,
    incrementar_partidas, guardar_partida, guardar_sesion,
    obtener_ultimas_partidas,
)
from profesor.ia_profesor import ProfesorIA
from motor.analizador import analizar_movimiento


def _formatear_historial(movimientos, color_jugador, nombre_jugador):
    """
    Convierte la lista plana de jugadas en texto etiquetado.
    Ejemplo: "1. Pablo: e4 | Oponente: e5  2. Pablo: Nf3 | Oponente: Nc6"
    """
    if not movimientos:
        return "Partida recién iniciada."

    jugador_es_blancas = color_jugador == "blancas"
    lineas = []

    for i in range(0, len(movimientos), 2):
        num = i // 2 + 1
        jug_blanca = movimientos[i] if i < len(movimientos) else "—"
        jug_negra  = movimientos[i + 1] if i + 1 < len(movimientos) else "—"

        if jugador_es_blancas:
            blanca_label = nombre_jugador
            negra_label  = "Oponente"
        else:
            blanca_label = "Oponente"
            negra_label  = nombre_jugador

        lineas.append(f"{num}. {blanca_label}: {jug_blanca}  {negra_label}: {jug_negra}")

    return " | ".join(lineas)

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "interfaz", "templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "interfaz", "static"),
)
app.secret_key = "tablero-nacho-secret-key"

# Estado global de la partida (single player, una instancia)
partida = {
    "tablero": None,
    "oponente": None,
    "profesor": None,
    "inicio": None,
    "color_jugador": "blancas",
    "modo_ensenanza": True,
}


@app.route("/")
def index():
    """Página principal — siempre muestra el tablero con modal de bienvenida."""
    jugador = obtener_jugador()
    # Si no hay perfil, creamos uno temporal para que el template funcione
    if not jugador:
        jugador = {"nombre": "", "nombre_profesor": "El Profe", "id": None}
    return render_template("tablero.html", jugador=jugador, mostrar_bienvenida=True)


@app.route("/api/setup", methods=["POST"])
def setup():
    """Crear perfil del jugador (flujo legacy)."""
    data = request.json
    nombre = data.get("nombre", "Jugador")
    edad = data.get("edad", 10)
    nombre_profesor = data.get("nombre_profesor", "El Profe")
    sabe_jugar = data.get("sabe_jugar", "aprendiendo")
    nivel = 2 if sabe_jugar == "si" else 1
    jugador_id = crear_jugador(nombre, edad, nombre_profesor, nivel)
    return jsonify({"ok": True, "jugador_id": jugador_id})


@app.route("/api/iniciar", methods=["POST"])
def iniciar():
    """Crea/actualiza perfil y arranca partida en un solo paso."""
    data = request.json
    nombre  = (data.get("nombre") or "Jugador").strip()
    nivel   = int(data.get("nivel", 1))
    color   = data.get("color", "blancas")
    velocidad = data.get("velocidad", "normal")

    # Crear o actualizar jugador
    jugador = obtener_jugador()
    if jugador:
        actualizar_jugador(jugador["id"], nombre=nombre, nivel=nivel)
        jugador_id = jugador["id"]
    else:
        jugador_id = crear_jugador(nombre, 12, "El Profe", nivel)

    jugador = obtener_jugador(jugador_id)

    # Iniciar partida
    partida["tablero"] = TableroAjedrez()
    partida["oponente"] = OponenteIA(nivel)
    partida["inicio"] = datetime.now()
    partida["color_jugador"] = color
    partida["modo_ensenanza"] = True
    partida["velocidad"] = velocidad

    try:
        partida["profesor"] = ProfesorIA(jugador_id)
    except Exception:
        partida["profesor"] = None

    if color == "negras":
        _mover_oponente()

    saludo = ""
    if partida["profesor"]:
        try:
            saludo = partida["profesor"].saludar(f"nueva sesión, nivel {nivel}, juega con {color}")
        except Exception:
            saludo = f"¡Hola {nombre}! ¡A jugar!"

    estado = partida["tablero"].obtener_estado()
    estado["en_partida"] = True
    estado["color_jugador"] = color
    estado["saludo_profesor"] = saludo
    estado["ultimo_movimiento"] = partida["tablero"].ultimo_movimiento()
    estado["historial_san"] = []
    estado["velocidad"] = velocidad
    return jsonify(estado)


@app.route("/api/estado")
def estado():
    """Estado actual del tablero."""
    if partida["tablero"] is None:
        return jsonify({"en_partida": False})

    estado = partida["tablero"].obtener_estado()
    estado["en_partida"] = True
    estado["color_jugador"] = partida["color_jugador"]
    estado["modo_ensenanza"] = partida["modo_ensenanza"]
    estado["nivel_oponente"] = partida["oponente"].info() if partida["oponente"] else None
    estado["ultimo_movimiento"] = partida["tablero"].ultimo_movimiento()

    # Casilla del rey en jaque
    if estado["es_jaque"]:
        turno_blancas = partida["tablero"].tablero.turn
        estado["rey_en_jaque"] = partida["tablero"].casilla_rey(turno_blancas)

    return jsonify(estado)


@app.route("/api/nueva_partida", methods=["POST"])
def nueva_partida():
    """Inicia una nueva partida."""
    jugador = obtener_jugador()
    if not jugador:
        return jsonify({"error": "No hay jugador configurado"}), 400

    data = request.json or {}
    nivel = data.get("nivel", jugador.get("nivel", 1))
    color = data.get("color", "blancas")

    partida["tablero"] = TableroAjedrez()
    partida["oponente"] = OponenteIA(nivel)
    partida["inicio"] = datetime.now()
    partida["color_jugador"] = color
    partida["modo_ensenanza"] = bool(jugador.get("modo_ensenanza", 1))

    # Inicializar profesor
    try:
        partida["profesor"] = ProfesorIA(jugador["id"])
    except Exception:
        partida["profesor"] = None

    # Si el jugador eligió negras, la IA mueve primero
    if color == "negras":
        _mover_oponente()

    # Saludo del profesor
    saludo = ""
    if partida["profesor"]:
        try:
            saludo = partida["profesor"].saludar(f"nueva partida nivel {nivel}")
        except Exception:
            saludo = f"¡Hola {jugador['nombre']}! ¡Vamos a jugar!"

    estado = partida["tablero"].obtener_estado()
    estado["en_partida"] = True
    estado["color_jugador"] = color
    estado["saludo_profesor"] = saludo
    estado["ultimo_movimiento"] = partida["tablero"].ultimo_movimiento()
    return jsonify(estado)


@app.route("/api/movimientos_validos")
def movimientos_validos():
    """Movimientos válidos para una casilla."""
    casilla = request.args.get("casilla")
    if not casilla or partida["tablero"] is None:
        return jsonify({"movimientos": []})
    movs = partida["tablero"].obtener_movimientos_validos(casilla)
    return jsonify({"movimientos": movs})


@app.route("/api/mover", methods=["POST"])
def mover():
    """Ejecuta un movimiento del jugador."""
    if partida["tablero"] is None:
        return jsonify({"error": "No hay partida en curso"}), 400

    data = request.json
    origen = data.get("origen")
    destino = data.get("destino")
    promocion = data.get("promocion")

    # Guardar FEN antes de mover (para análisis Stockfish)
    fen_antes = partida["tablero"].obtener_fen()
    turno_blancas = partida["tablero"].tablero.turn  # True=blancas

    resultado_mov = partida["tablero"].mover_pieza(origen, destino, promocion)
    if resultado_mov is None:
        return jsonify({"error": "Movimiento inválido"}), 400

    fen_despues = partida["tablero"].obtener_fen()

    respuesta = {
        "movimiento": resultado_mov,
        "estado": partida["tablero"].obtener_estado(),
        "comentario_profesor": "",
        "movimiento_oponente": None,
    }

    # Análisis Stockfish siempre (es rápido y lo usamos para decidir si habla el profe)
    analisis = None
    try:
        analisis = analizar_movimiento(fen_antes, fen_despues, turno_blancas)
        resultado_mov["analisis"] = analisis
    except Exception:
        pass

    # El profe habla SOLO en situaciones importantes
    def _debe_hablar_profe():
        if not partida["modo_ensenanza"] or not partida["profesor"]:
            return False
        if not analisis:
            return resultado_mov.get("es_jaque_mate")
        calidad = analisis.get("calidad")
        if calidad == "blunder":
            return True
        if analisis.get("captura_perdida"):
            return True
        if resultado_mov.get("es_jaque_mate"):
            return True
        return False

    if _debe_hablar_profe():
        try:
            jugador = obtener_jugador()
            historial_fmt = _formatear_historial(
                partida["tablero"].historial_movimientos(),
                partida["color_jugador"],
                jugador["nombre"] if jugador else "Vos",
            )
            comentario = partida["profesor"].comentar_movimiento(
                partida["tablero"].obtener_fen(),
                historial_fmt,
                resultado_mov,
            )
            respuesta["comentario_profesor"] = comentario
        except Exception:
            pass

    # Si la partida no terminó, el oponente mueve
    if not partida["tablero"].es_fin_de_partida():
        mov_oponente = _mover_oponente()
        if mov_oponente:
            respuesta["movimiento_oponente"] = mov_oponente
            respuesta["estado"] = partida["tablero"].obtener_estado()

    # Si terminó la partida después del movimiento
    if partida["tablero"].es_fin_de_partida():
        respuesta["fin_partida"] = _finalizar_partida()

    respuesta["estado"]["ultimo_movimiento"] = partida["tablero"].ultimo_movimiento()
    respuesta["estado"]["en_partida"] = not partida["tablero"].es_fin_de_partida()
    respuesta["estado"]["color_jugador"] = partida["color_jugador"]
    respuesta["estado"]["historial_san"] = partida["tablero"].historial_movimientos()

    # Rey en jaque
    if respuesta["estado"]["es_jaque"]:
        turno_blancas = partida["tablero"].tablero.turn
        respuesta["estado"]["rey_en_jaque"] = partida["tablero"].casilla_rey(turno_blancas)

    return jsonify(respuesta)


@app.route("/api/deshacer", methods=["POST"])
def deshacer():
    """Deshace el último movimiento (2 veces: oponente + jugador)."""
    if partida["tablero"] is None:
        return jsonify({"error": "No hay partida"}), 400

    # Deshacer movimiento del oponente y del jugador
    partida["tablero"].deshacer()
    partida["tablero"].deshacer()

    estado = partida["tablero"].obtener_estado()
    estado["en_partida"] = True
    estado["color_jugador"] = partida["color_jugador"]
    estado["ultimo_movimiento"] = partida["tablero"].ultimo_movimiento()
    return jsonify({"ok": True, "estado": estado})


@app.route("/api/consejo", methods=["POST"])
def consejo():
    """El jugador pide consejo al profesor."""
    if partida["tablero"] is None or partida["profesor"] is None:
        return jsonify({"consejo": "¡Pensá bien tu próximo movimiento!"})

    try:
        jugador = obtener_jugador()
        historial_fmt = _formatear_historial(
            partida["tablero"].historial_movimientos(),
            partida["color_jugador"],
            jugador["nombre"] if jugador else "Vos",
        )
        texto = partida["profesor"].dar_consejo(
            partida["tablero"].obtener_fen(),
            historial_fmt,
            partida["tablero"].turno_actual(),
        )
    except Exception:
        texto = "Mirá bien el tablero... ¿hay alguna pieza que puedas mejorar?"

    return jsonify({"consejo": texto})


@app.route("/api/chat", methods=["POST"])
def chat():
    """El jugador envía un mensaje al profesor."""
    if partida["profesor"] is None:
        return jsonify({"respuesta": "El profesor no está disponible ahora."})

    data = request.json
    mensaje = data.get("mensaje", "")

    fen = partida["tablero"].obtener_fen() if partida["tablero"] else "inicio"
    jugador = obtener_jugador()
    historial_fmt = _formatear_historial(
        partida["tablero"].historial_movimientos() if partida["tablero"] else [],
        partida["color_jugador"],
        jugador["nombre"] if jugador else "Vos",
    )

    try:
        respuesta = partida["profesor"].responder_chat(fen, historial_fmt, mensaje)
    except Exception:
        respuesta = "¡Disculpá! No pude pensar bien esa. ¿Me repetís?"

    return jsonify({"respuesta": respuesta})


@app.route("/api/rendirse", methods=["POST"])
def rendirse():
    """El jugador se rinde."""
    if partida["tablero"] is None:
        return jsonify({"error": "No hay partida"}), 400

    resultado = _finalizar_partida(resultado_forzado="abandonada")
    return jsonify({"ok": True, "fin_partida": resultado})


@app.route("/api/toggle_ensenanza", methods=["POST"])
def toggle_ensenanza():
    """Activa/desactiva modo enseñanza."""
    partida["modo_ensenanza"] = not partida["modo_ensenanza"]
    jugador = obtener_jugador()
    if jugador:
        actualizar_jugador(jugador["id"], modo_ensenanza=1 if partida["modo_ensenanza"] else 0)
    return jsonify({"modo_ensenanza": partida["modo_ensenanza"]})


@app.route("/api/cambiar_nivel", methods=["POST"])
def cambiar_nivel():
    """Cambia el nivel del oponente."""
    data = request.json
    nivel = data.get("nivel", 1)
    if partida["oponente"]:
        partida["oponente"].cambiar_nivel(nivel)
    jugador = obtener_jugador()
    if jugador:
        actualizar_jugador(jugador["id"], nivel=nivel)
    return jsonify({"ok": True, "nivel": nivel})


@app.route("/api/jugador")
def api_jugador():
    """Info del jugador."""
    jugador = obtener_jugador()
    if not jugador:
        return jsonify({"existe": False})
    jugador["existe"] = True
    return jsonify(jugador)


# --- Funciones internas ---

def _mover_oponente():
    """La IA hace su movimiento."""
    if partida["oponente"] is None or partida["tablero"] is None:
        return None
    if partida["tablero"].es_fin_de_partida():
        return None

    mov = partida["oponente"].elegir_movimiento(partida["tablero"].tablero)
    if mov is None:
        return None

    origen = mov.from_square
    destino = mov.to_square
    promocion = None
    if mov.promotion:
        promo_map = {5: "q", 4: "r", 3: "b", 2: "n"}
        promocion = promo_map.get(mov.promotion)

    import chess
    resultado = partida["tablero"].mover_pieza(
        chess.square_name(origen),
        chess.square_name(destino),
        promocion,
    )
    return resultado


def _finalizar_partida(resultado_forzado=None):
    """Guarda la partida y genera resumen."""
    jugador = obtener_jugador()
    if not jugador or partida["tablero"] is None:
        return {}

    if resultado_forzado:
        resultado = resultado_forzado
    else:
        res = partida["tablero"].resultado()
        if partida["color_jugador"] == "blancas":
            if res == "victoria_blancas":
                resultado = "victoria"
            elif res == "victoria_negras":
                resultado = "derrota"
            else:
                resultado = "empate"
        else:
            if res == "victoria_negras":
                resultado = "victoria"
            elif res == "victoria_blancas":
                resultado = "derrota"
            else:
                resultado = "empate"

    # Duración
    duracion = None
    if partida["inicio"]:
        duracion = int((datetime.now() - partida["inicio"]).total_seconds() / 60)

    # PGN
    pgn = partida["tablero"].obtener_pgn()

    # Resumen del profesor
    resumen_profesor = ""
    resumen_interno = ""
    if partida["profesor"]:
        try:
            historial_fmt = _formatear_historial(
                partida["tablero"].historial_movimientos(),
                partida["color_jugador"],
                jugador["nombre"] if jugador else "Vos",
            )
            res_prof = partida["profesor"].resumir_partida(
                partida["tablero"].obtener_fen(),
                historial_fmt,
                resultado,
            )
            resumen_profesor = res_prof["mensaje"]
            resumen_interno = res_prof.get("resumen_interno", "")
        except Exception:
            resumen_profesor = "¡Buena partida! Seguimos la próxima."

    # Guardar en DB
    nivel = partida["oponente"].nivel if partida["oponente"] else 1
    guardar_partida(jugador["id"], resultado, pgn, nivel, duracion, resumen_interno)
    incrementar_partidas(jugador["id"], victoria=(resultado == "victoria"))

    # Guardar sesión
    guardar_sesion(
        jugador["id"],
        resumen_interno or f"Partida: {resultado}",
        conceptos_trabajados=None,
        estado_animo=None,
    )

    return {
        "resultado": resultado,
        "resumen_profesor": resumen_profesor,
        "duracion": duracion,
        "pgn": pgn,
    }


if __name__ == "__main__":
    inicializar_db()
    print(f"Tablero Nacho corriendo en http://localhost:{PUERTO_WEB}")
    app.run(host="0.0.0.0", port=PUERTO_WEB, debug=True)
