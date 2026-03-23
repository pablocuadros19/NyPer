import os
from dotenv import load_dotenv

load_dotenv()

# API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODELO_PROFESOR = "llama-3.3-70b-versatile"

# Base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "tablero_nacho.db")

# Stockfish
STOCKFISH_PATH = os.path.join(os.path.dirname(__file__), "stockfish", "stockfish.exe")
STOCKFISH_TIEMPO_ANALISIS = 0.1  # segundos por movimiento

# Interfaz
TAMANO_CASILLA = 80  # px mínimo por casilla
PUERTO_WEB = 5000

# Niveles de oponente (depth de búsqueda)
NIVELES_OPONENTE = {
    1: {"nombre": "Aprendiz", "depth": 1, "error_rate": 0.4},
    2: {"nombre": "Compañero", "depth": 3, "error_rate": 0.15},
    3: {"nombre": "Desafío", "depth": 6, "error_rate": 0.0},
}
