"""
Descarga el set de piezas "Maestro" desde Lichess (licencia libre).
Correr una sola vez: python descargar_piezas.py
"""

import urllib.request
import os

BASE_URL = "https://raw.githubusercontent.com/lichess-org/lila/master/public/piece/maestro"
DIRECTORIO = os.path.join(os.path.dirname(__file__), "interfaz", "static", "assets", "piezas")

os.makedirs(DIRECTORIO, exist_ok=True)

piezas = ['K', 'Q', 'R', 'B', 'N', 'P']
colores = ['w', 'b']

print("Descargando set Maestro...")
for color in colores:
    for pieza in piezas:
        nombre = f"{color}{pieza}.svg"
        url = f"{BASE_URL}/{nombre}"
        destino = os.path.join(DIRECTORIO, nombre)
        print(f"  {nombre}...", end=" ")
        try:
            urllib.request.urlretrieve(url, destino)
            print("OK")
        except Exception as e:
            print(f"ERROR: {e}")

print(f"\nListo. Piezas en: {DIRECTORIO}")
