"""
Motor de ajedrez — wrapper limpio sobre python-chess.
No sabe nada de interfaz, LEDs ni profesor.
"""

import chess

# Mapeo de nombres de piezas al español
NOMBRES_PIEZAS = {
    chess.PAWN: "peón",
    chess.KNIGHT: "caballo",
    chess.BISHOP: "alfil",
    chess.ROOK: "torre",
    chess.QUEEN: "dama",
    chess.KING: "rey",
}

NOMBRES_COLUMNAS = {0: "a", 1: "b", 2: "c", 3: "d", 4: "e", 5: "f", 6: "g", 7: "h"}


def nombre_casilla_es(casilla):
    """Convierte casilla (0-63) a notación legible: 'e4', 'a1', etc."""
    return chess.square_name(casilla)


def nombre_pieza_es(pieza):
    """Devuelve nombre en español de una pieza."""
    if pieza is None:
        return None
    return NOMBRES_PIEZAS.get(pieza.piece_type, "pieza")


def color_es(color):
    """True -> 'blancas', False -> 'negras'."""
    return "blancas" if color else "negras"


class TableroAjedrez:
    """Interfaz limpia del motor de ajedrez."""

    def __init__(self):
        self.tablero = chess.Board()

    def obtener_movimientos_validos(self, casilla=None):
        """
        Devuelve movimientos válidos.
        Si se pasa una casilla (str como 'e2' o int 0-63), filtra por esa casilla.
        Retorna lista de dicts con origen, destino, notación.
        """
        movimientos = []
        for mov in self.tablero.legal_moves:
            if casilla is not None:
                # Convertir casilla str a int si es necesario
                sq = chess.parse_square(casilla) if isinstance(casilla, str) else casilla
                if mov.from_square != sq:
                    continue
            movimientos.append({
                "origen": chess.square_name(mov.from_square),
                "destino": chess.square_name(mov.to_square),
                "notacion": self.tablero.san(mov),
                "es_captura": self.tablero.is_capture(mov),
                "es_enroque": self.tablero.is_castling(mov),
            })
        return movimientos

    def mover_pieza(self, origen, destino, promocion=None):
        """
        Ejecuta un movimiento. Retorna info del movimiento o None si es inválido.
        origen/destino: str ('e2', 'e4') o int (0-63).
        promocion: str opcional ('q', 'r', 'b', 'n') para promoción de peón.
        """
        if isinstance(origen, str):
            origen = chess.parse_square(origen)
        if isinstance(destino, str):
            destino = chess.parse_square(destino)

        # Determinar si es promoción
        promo_piece = None
        if promocion:
            promo_map = {"q": chess.QUEEN, "r": chess.ROOK, "b": chess.BISHOP, "n": chess.KNIGHT}
            promo_piece = promo_map.get(promocion.lower())

        # Si es peón llegando a última fila, promocionar a dama por defecto
        pieza = self.tablero.piece_at(origen)
        if pieza and pieza.piece_type == chess.PAWN:
            fila_destino = chess.square_rank(destino)
            if (pieza.color == chess.WHITE and fila_destino == 7) or \
               (pieza.color == chess.BLACK and fila_destino == 0):
                if promo_piece is None:
                    promo_piece = chess.QUEEN

        movimiento = chess.Move(origen, destino, promotion=promo_piece)

        if movimiento not in self.tablero.legal_moves:
            return None

        # Guardar info antes de mover
        pieza_capturada = self.tablero.piece_at(destino)
        san = self.tablero.san(movimiento)
        es_jaque = self.tablero.gives_check(movimiento)

        self.tablero.push(movimiento)

        return {
            "notacion": san,
            "origen": chess.square_name(origen),
            "destino": chess.square_name(destino),
            "pieza": nombre_pieza_es(pieza),
            "captura": nombre_pieza_es(pieza_capturada),
            "es_jaque": es_jaque,
            "es_jaque_mate": self.tablero.is_checkmate(),
            "es_tablas": self.tablero.is_stalemate() or self.tablero.is_insufficient_material(),
        }

    def deshacer(self):
        """Deshace el último movimiento. Retorna True si se pudo."""
        if len(self.tablero.move_stack) == 0:
            return False
        self.tablero.pop()
        return True

    def obtener_estado(self):
        """Retorna estado completo del tablero como dict."""
        piezas = {}
        for sq in chess.SQUARES:
            pieza = self.tablero.piece_at(sq)
            if pieza:
                piezas[chess.square_name(sq)] = {
                    "tipo": pieza.symbol().lower(),
                    "color": "blancas" if pieza.color == chess.WHITE else "negras",
                    "simbolo": pieza.symbol(),
                    "nombre": nombre_pieza_es(pieza),
                }

        return {
            "fen": self.tablero.fen(),
            "piezas": piezas,
            "turno": color_es(self.tablero.turn),
            "es_jaque": self.tablero.is_check(),
            "es_jaque_mate": self.tablero.is_checkmate(),
            "es_tablas": self.tablero.is_stalemate() or self.tablero.is_insufficient_material(),
            "movimiento_numero": self.tablero.fullmove_number,
            "puede_deshacer": len(self.tablero.move_stack) > 0,
        }

    def es_jaque(self):
        return self.tablero.is_check()

    def es_jaque_mate(self):
        return self.tablero.is_checkmate()

    def es_fin_de_partida(self):
        return self.tablero.is_game_over()

    def resultado(self):
        """Retorna el resultado si la partida terminó."""
        if not self.tablero.is_game_over():
            return None
        result = self.tablero.result()
        if result == "1-0":
            return "victoria_blancas"
        elif result == "0-1":
            return "victoria_negras"
        return "empate"

    def historial_movimientos(self):
        """Retorna lista de movimientos en notación algebraica."""
        movimientos = []
        tablero_temp = chess.Board()
        for mov in self.tablero.move_stack:
            san = tablero_temp.san(mov)
            movimientos.append(san)
            tablero_temp.push(mov)
        return movimientos

    def turno_actual(self):
        return color_es(self.tablero.turn)

    def obtener_fen(self):
        return self.tablero.fen()

    def obtener_pgn(self):
        """Retorna la partida en formato PGN."""
        import chess.pgn
        import io
        game = chess.pgn.Game()
        node = game
        for mov in self.tablero.move_stack:
            node = node.add_variation(mov)
        exporter = chess.pgn.StringExporter(headers=False)
        return game.accept(exporter)

    def cargar_fen(self, fen):
        """Carga una posición desde FEN."""
        self.tablero.set_fen(fen)

    def nueva_partida(self):
        """Reinicia el tablero."""
        self.tablero.reset()

    def casilla_rey(self, color_blancas=True):
        """Retorna la casilla del rey del color indicado."""
        color = chess.WHITE if color_blancas else chess.BLACK
        sq = self.tablero.king(color)
        return chess.square_name(sq) if sq is not None else None

    def ultimo_movimiento(self):
        """Retorna origen y destino del último movimiento."""
        if not self.tablero.move_stack:
            return None
        mov = self.tablero.move_stack[-1]
        return {
            "origen": chess.square_name(mov.from_square),
            "destino": chess.square_name(mov.to_square),
        }
