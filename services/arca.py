"""
Consulta datos fiscales de contribuyentes via CuitOnline.
Versión optimizada con consultas paralelas y cache.
"""

import httpx
import re
import json
import os
import time
import threading
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

CACHE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cache_arca.json")
CACHE_HORAS = 24


def _cargar_cache():
    if not os.path.exists(CACHE_PATH):
        return {}
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        limite = (datetime.now() - timedelta(hours=CACHE_HORAS)).isoformat()
        return {k: v for k, v in cache.items() if v.get("_fecha", "") > limite}
    except Exception:
        return {}


def _guardar_cache(cache):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _consultar_http(cuit_limpio: str) -> dict:
    """Request HTTP + parsing, sin manejo de cache."""
    url = f"https://www.cuitonline.com/search.php?q={cuit_limpio}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    for intento in range(3):
        try:
            with httpx.Client(verify=False, timeout=10, follow_redirects=True) as client:
                r = client.get(url, headers=headers)

            if r.status_code != 200:
                if intento < 2:
                    time.sleep(2)
                    continue
                return {"arca_consultado": False, "arca_error": f"HTTP {r.status_code}"}

            soup = BeautifulSoup(r.text, "html.parser")
            hits = soup.find_all("div", class_="hit")

            if not hits:
                return {
                    "arca_consultado": True,
                    "arca_estado_clave": "NO_ENCONTRADO",
                    "arca_denominacion": "",
                    "arca_condicion_iva": "",
                    "arca_tipo_persona": "",
                    "arca_empleador": False,
                    "arca_ganancias": False,
                    "arca_fecha_consulta": datetime.now().isoformat(),
                    "_fecha": datetime.now().isoformat(),
                }

            hit = hits[0]
            text = hit.get_text(separator="|", strip=True)

            denom_tag = hit.find("a", class_="denominacion") or hit.find("h2", class_="denominacion")
            denominacion = denom_tag.get_text(strip=True) if denom_tag else ""

            tipo_persona = ""
            tipo_match = re.search(r"Persona\s+(Jur.dica|F.sica)", text, re.IGNORECASE)
            if tipo_match:
                raw = tipo_match.group(1).lower()
                tipo_persona = "juridica" if "jur" in raw else "fisica"

            condicion_iva = ""
            iva_match = re.search(r"IVA:\s*([^|]+)", text)
            if iva_match:
                iva_raw = iva_match.group(1).strip().lower()
                if "inscripto" in iva_raw or "inscript" in iva_raw:
                    condicion_iva = "Responsable Inscripto"
                elif "exento" in iva_raw:
                    condicion_iva = "IVA Exento"
                elif "no responsable" in iva_raw:
                    condicion_iva = "No Responsable"
                else:
                    condicion_iva = iva_match.group(1).strip()

            if not condicion_iva:
                mono_match = re.search(r"Monotributo", text, re.IGNORECASE)
                if mono_match:
                    condicion_iva = "Monotributo"

            empleador = "Empleador" in text
            ganancias = "Ganancias" in text

            return {
                "arca_consultado": True,
                "arca_estado_clave": "ACTIVO",
                "arca_denominacion": denominacion,
                "arca_condicion_iva": condicion_iva,
                "arca_tipo_persona": tipo_persona,
                "arca_empleador": empleador,
                "arca_ganancias": ganancias,
                "arca_fecha_consulta": datetime.now().isoformat(),
                "_fecha": datetime.now().isoformat(),
            }

        except (httpx.TimeoutException, httpx.ConnectError):
            if intento < 2:
                time.sleep(2)
                continue
            return {"arca_consultado": False, "arca_error": "Timeout/conexión"}
        except Exception as e:
            return {"arca_consultado": False, "arca_error": str(e)}

    return {"arca_consultado": False, "arca_error": "Reintentos agotados"}


def consultar_arca(cuit: str) -> dict:
    """Consulta individual con cache en disco."""
    cuit_limpio = re.sub(r"[^0-9]", "", cuit)
    if len(cuit_limpio) != 11:
        return {"arca_consultado": False, "arca_error": "CUIT inválido"}

    cache = _cargar_cache()
    if cuit_limpio in cache:
        return cache[cuit_limpio]

    resultado = _consultar_http(cuit_limpio)
    cache[cuit_limpio] = resultado
    _guardar_cache(cache)
    return resultado


def enriquecer_arca(comercio: dict) -> dict:
    """Enriquece un comercio con datos de ARCA/CuitOnline."""
    cuit = comercio.get("cuit", "")
    if not cuit or len(re.sub(r"[^0-9]", "", cuit)) != 11:
        return comercio
    datos = consultar_arca(cuit)
    comercio.update(datos)
    return comercio


def enriquecer_arca_lote(comercios: list, max_workers: int = 3, callback=None) -> tuple:
    """
    Enriquece comercios en paralelo con CuitOnline.
    ~5x más rápido que secuencial gracias a workers concurrentes.
    callback(actual, total) para progreso.
    """
    cache = _cargar_cache()
    lock = threading.Lock()

    # Separar: ya consultados / en cache / pendientes HTTP
    pendientes = []
    for c in comercios:
        cuit = c.get("cuit", "")
        if not cuit or c.get("arca_consultado"):
            continue
        cuit_limpio = re.sub(r"[^0-9]", "", cuit)
        if len(cuit_limpio) != 11:
            continue
        # Si está en cache, aplicar directo (sin HTTP)
        if cuit_limpio in cache:
            c.update(cache[cuit_limpio])
            continue
        pendientes.append((c, cuit_limpio))

    total = len(comercios)
    procesados = [total - len(pendientes)]

    if callback:
        callback(procesados[0], total)

    def worker(comercio, cuit_limpio):
        resultado = _consultar_http(cuit_limpio)
        comercio.update(resultado)
        with lock:
            if resultado.get("arca_consultado"):
                cache[cuit_limpio] = resultado
            procesados[0] += 1

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for c, cuit in pendientes:
            futures.append(executor.submit(worker, c, cuit))
            # Escalonar envíos: ~4 req/s para no saturar CuitOnline
            time.sleep(0.25)
            if callback:
                callback(procesados[0], total)

        # Esperar los que queden en vuelo
        for f in futures:
            try:
                f.result(timeout=30)
            except Exception:
                pass
            if callback:
                callback(procesados[0], total)

    _guardar_cache(cache)
    enriquecidos = sum(1 for c in comercios if c.get("arca_consultado"))
    return comercios, enriquecidos


# --- Test rápido ---
if __name__ == "__main__":
    tests = [
        ("30656461825", "Melar SA"),
        ("33708140479", "Exducere SRL"),
        ("99999999999", "CUIT inválido"),
    ]

    for cuit, desc in tests:
        print(f"\n{'='*50}")
        print(f"{desc} ({cuit})")
        print("=" * 50)
        resultado = consultar_arca(cuit)
        for k, v in resultado.items():
            if not k.startswith("_"):
                print(f"  {k}: {v}")
        time.sleep(1)
