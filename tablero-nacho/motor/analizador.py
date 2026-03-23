"""
Analizador de movimientos con Stockfish.
Evalúa la calidad de cada jugada y provee datos al profesor.
"""

import chess
import chess.engine
import os

from config import STOCKFISH_PATH, STOCKFISH_TIEMPO_ANALISIS

UMBRAL_BLUNDER     = 200
UMBRAL_ERROR       = 100
UMBRAL_IMPRECISION = 50


def clasificar_calidad(perdida_cp):
    if perdida_cp >= UMBRAL_BLUNDER:
        return "blunder"
    elif perdida_cp >= UMBRAL_ERROR:
        return "error"
    elif perdida_cp >= UMBRAL_IMPRECISION:
        return "imprecision"
    return "buena"


def analizar_movimiento(fen_antes, fen_despues, turno_blancas, movimiento_uci=None):
    """
    Analiza la calidad de un movimiento.
    Retorna dict con calidad, pérdida en cp, mejor jugada y si había captura disponible.
    """
    if not os.path.exists(os.path.abspath(STOCKFISH_PATH)):
        return None

    try:
        with chess.engine.SimpleEngine.popen_uci(os.path.abspath(STOCKFISH_PATH)) as engine:
            limite = chess.engine.Limit(time=STOCKFISH_TIEMPO_ANALISIS)

            tablero_antes = chess.Board(fen_antes)

            # Análisis ANTES del movimiento — para obtener mejor jugada
            info_antes = engine.analyse(tablero_antes, limite)
            score_antes = info_antes["score"].white()
            mejor_jugada_mov = info_antes.get("pv", [None])[0]
            mejor_jugada_san = tablero_antes.san(mejor_jugada_mov) if mejor_jugada_mov else None
            mejor_era_captura = bool(mejor_jugada_mov and tablero_antes.is_capture(mejor_jugada_mov))

            # El jugador capturó?
            tablero_despues = chess.Board(fen_despues)
            piezas_antes = len(tablero_antes.piece_map())
            piezas_despues = len(tablero_despues.piece_map())
            jugador_capturo = piezas_despues < piezas_antes

            # Análisis DESPUÉS del movimiento — para calcular pérdida
            info_despues = engine.analyse(tablero_despues, limite)
            score_despues = info_despues["score"].white()

            cp_antes = score_antes.score(mate_score=10000)
            cp_despues = score_despues.score(mate_score=10000)

            if cp_antes is None or cp_despues is None:
                perdida_cp = 0
            elif turno_blancas:
                perdida_cp = max(0, cp_antes - cp_despues)
            else:
                perdida_cp = max(0, cp_despues - cp_antes)

            # Captura perdida: la mejor era comer y el jugador no comió
            captura_perdida = mejor_era_captura and not jugador_capturo and perdida_cp >= UMBRAL_ERROR

            return {
                "calidad": clasificar_calidad(perdida_cp),
                "perdida_cp": perdida_cp,
                "mejor_jugada_alternativa": mejor_jugada_san,
                "mejor_era_captura": mejor_era_captura,
                "captura_perdida": captura_perdida,
            }

    except Exception:
        return None
