"""
Oponente IA — usa python-chess para evaluar movimientos.
Sin Stockfish para simplificar instalación (se puede agregar después).
"""

import chess
import random

from config import NIVELES_OPONENTE


# Valores de piezas para evaluación básica
VALOR_PIEZA = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}

# Bonus por posición central
BONUS_CENTRO = {
    chess.E4: 20, chess.D4: 20, chess.E5: 20, chess.D5: 20,
    chess.C3: 10, chess.D3: 10, chess.E3: 10, chess.F3: 10,
    chess.C4: 10, chess.F4: 10, chess.C5: 10, chess.F5: 10,
    chess.C6: 10, chess.D6: 10, chess.E6: 10, chess.F6: 10,
}


def evaluar_tablero(tablero):
    """Evaluación simple del tablero desde perspectiva de blancas."""
    if tablero.is_checkmate():
        return -9999 if tablero.turn == chess.WHITE else 9999
    if tablero.is_stalemate() or tablero.is_insufficient_material():
        return 0

    valor = 0
    for sq in chess.SQUARES:
        pieza = tablero.piece_at(sq)
        if pieza is None:
            continue
        v = VALOR_PIEZA.get(pieza.piece_type, 0)
        v += BONUS_CENTRO.get(sq, 0)
        # Bonus por movilidad
        if pieza.color == chess.WHITE:
            valor += v
        else:
            valor -= v

    return valor


def minimax(tablero, depth, alpha, beta, maximizando):
    """Minimax con poda alfa-beta."""
    if depth == 0 or tablero.is_game_over():
        return evaluar_tablero(tablero), None

    mejor_mov = None

    if maximizando:
        max_eval = float("-inf")
        movimientos = list(tablero.legal_moves)
        # Ordenar: capturas primero para mejor poda
        movimientos.sort(key=lambda m: tablero.is_capture(m), reverse=True)
        for mov in movimientos:
            tablero.push(mov)
            eval_pos, _ = minimax(tablero, depth - 1, alpha, beta, False)
            tablero.pop()
            if eval_pos > max_eval:
                max_eval = eval_pos
                mejor_mov = mov
            alpha = max(alpha, eval_pos)
            if beta <= alpha:
                break
        return max_eval, mejor_mov
    else:
        min_eval = float("inf")
        movimientos = list(tablero.legal_moves)
        movimientos.sort(key=lambda m: tablero.is_capture(m), reverse=True)
        for mov in movimientos:
            tablero.push(mov)
            eval_pos, _ = minimax(tablero, depth - 1, alpha, beta, True)
            tablero.pop()
            if eval_pos < min_eval:
                min_eval = eval_pos
                mejor_mov = mov
            beta = min(beta, eval_pos)
            if beta <= alpha:
                break
        return min_eval, mejor_mov


class OponenteIA:
    """Oponente con niveles de dificultad configurables."""

    def __init__(self, nivel=1):
        self.cambiar_nivel(nivel)

    def cambiar_nivel(self, nivel):
        config = NIVELES_OPONENTE.get(nivel, NIVELES_OPONENTE[1])
        self.nivel = nivel
        self.depth = config["depth"]
        self.error_rate = config["error_rate"]
        self.nombre_nivel = config["nombre"]

    def elegir_movimiento(self, tablero_chess):
        """
        Elige un movimiento dado un tablero chess.Board.
        Retorna un chess.Move.
        """
        movimientos = list(tablero_chess.legal_moves)
        if not movimientos:
            return None

        # ¿Cometer error intencional?
        if random.random() < self.error_rate:
            return random.choice(movimientos)

        # Jugar con minimax
        maximizando = tablero_chess.turn == chess.WHITE
        _, mejor = minimax(tablero_chess, self.depth, float("-inf"), float("inf"), maximizando)

        return mejor if mejor else random.choice(movimientos)

    def info(self):
        return {
            "nivel": self.nivel,
            "nombre": self.nombre_nivel,
            "depth": self.depth,
        }
