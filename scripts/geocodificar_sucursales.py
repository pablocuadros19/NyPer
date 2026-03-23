"""
Script one-shot para geocodificar sucursales de Banco Provincia.
Lee data/sucursales.json, agrega lat/lng via Google Geocoding API.
Ejecutar una sola vez: python scripts/geocodificar_sucursales.py
"""
import json
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
if not API_KEY:
    print("ERROR: GOOGLE_MAPS_API_KEY no encontrada en .env")
    exit(1)

ARCHIVO = os.path.join(os.path.dirname(__file__), "..", "data", "sucursales.json")

with open(ARCHIVO, "r", encoding="utf-8") as f:
    sucursales = json.load(f)

total = len(sucursales)
sin_coords = [s for s in sucursales if s["lat"] is None]
print(f"Total: {total} | Sin coordenadas: {len(sin_coords)}")

if not sin_coords:
    print("Todas las sucursales ya tienen coordenadas.")
    exit(0)

exitos = 0
fallos = 0

for i, suc in enumerate(sin_coords):
    # Armar dirección completa para mejor precisión
    direccion = f"{suc['domicilio']}, {suc['localidad']}, {suc['partido']}, Buenos Aires, Argentina"

    try:
        resp = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": direccion, "key": API_KEY},
            timeout=10
        )
        data = resp.json()

        if data["status"] == "OK" and data["results"]:
            loc = data["results"][0]["geometry"]["location"]
            suc["lat"] = round(loc["lat"], 6)
            suc["lng"] = round(loc["lng"], 6)
            exitos += 1
            print(f"  [{i+1}/{len(sin_coords)}] OK: {suc['nombre']} → ({suc['lat']}, {suc['lng']})")
        else:
            fallos += 1
            print(f"  [{i+1}/{len(sin_coords)}] FALLO: {suc['nombre']} — {data['status']}")
    except Exception as e:
        fallos += 1
        print(f"  [{i+1}/{len(sin_coords)}] ERROR: {suc['nombre']} — {e}")

    # Guardar parcial cada 50
    if (i + 1) % 50 == 0:
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            json.dump(sucursales, f, ensure_ascii=False, indent=2)
        print(f"  >>> Guardado parcial ({i+1}/{len(sin_coords)})")

    time.sleep(0.1)

# Guardar final
with open(ARCHIVO, "w", encoding="utf-8") as f:
    json.dump(sucursales, f, ensure_ascii=False, indent=2)

print(f"\nResultado: {exitos} OK, {fallos} fallos de {len(sin_coords)} total")
print(f"Archivo actualizado: {ARCHIVO}")
