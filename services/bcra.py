"""
Consulta BCRA Central de Deudores + Cheques Rechazados.
Versión optimizada con consultas paralelas y cache 24h.
"""

import httpx
import re
import json
import os
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

SITUACION_TEXTOS = {
    0: "Sin deudas registradas",
    1: "Normal",
    2: "Con seguimiento especial",
    3: "Con problemas",
    4: "Alto riesgo de insolvencia",
    5: "Irrecuperable",
    6: "Irrecuperable por disposición técnica",
}

BCRA_TOKEN = os.getenv("BCRA_TOKEN", "")
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}
if BCRA_TOKEN:
    HEADERS["Authorization"] = f"BEARER {BCRA_TOKEN}"

CACHE_BCRA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cache_bcra.json")
CACHE_HORAS = 24


def _cargar_cache_bcra():
    if not os.path.exists(CACHE_BCRA_PATH):
        return {}
    try:
        with open(CACHE_BCRA_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        limite = (datetime.now() - timedelta(hours=CACHE_HORAS)).isoformat()
        return {k: v for k, v in cache.items() if v.get("_fecha", "") > limite}
    except Exception:
        return {}


def _guardar_cache_bcra(cache):
    os.makedirs(os.path.dirname(CACHE_BCRA_PATH), exist_ok=True)
    with open(CACHE_BCRA_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _hacer_request(url: str, max_reintentos: int = 3) -> httpx.Response | None:
    """Request con reintentos, backoff y manejo de 429."""
    for intento in range(max_reintentos + 1):
        try:
            with httpx.Client(verify=False, timeout=15) as client:
                r = client.get(url, headers=HEADERS)
                if r.status_code == 429:
                    # Rate limited — esperar más en cada reintento
                    espera = 5 * (intento + 1)
                    time.sleep(espera)
                    continue
                return r
        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError):
            if intento < max_reintentos:
                time.sleep(3 * (intento + 1))
                continue
    return None


def consultar_deudas(cuit: str) -> dict:
    """Consulta Central de Deudores. Captura últimos 6 períodos con detalle."""
    url = f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Deudas/{cuit}"
    r = _hacer_request(url)

    if r is None:
        return {"bcra_situacion": -1, "bcra_situacion_texto": "Error conexión"}

    if r.status_code == 404:
        return {
            "bcra_situacion": 0,
            "bcra_situacion_texto": "Sin deudas registradas",
            "bcra_monto_total": 0,
            "bcra_entidades": 0,
            "bcra_detalle": [],
            "bcra_periodos": [],
            "bcra_evolucion": "sin_historial",
            "bcra_proceso_concursal": False,
            "bcra_situacion_juridica": False,
        }

    if r.status_code != 200:
        return {"bcra_situacion": -1, "bcra_situacion_texto": f"Error HTTP {r.status_code}"}

    try:
        data = r.json()
    except Exception:
        return {"bcra_situacion": -1, "bcra_situacion_texto": "Error parseando JSON"}

    periodos = data.get("results", {}).get("periodos", [])

    if not periodos:
        return {
            "bcra_situacion": 0,
            "bcra_situacion_texto": "Sin deudas registradas",
            "bcra_monto_total": 0,
            "bcra_entidades": 0,
            "bcra_detalle": [],
            "bcra_periodos": [],
            "bcra_evolucion": "sin_historial",
            "bcra_proceso_concursal": False,
            "bcra_situacion_juridica": False,
        }

    periodos_detalle = []
    for periodo in periodos[:6]:
        entidades = periodo.get("entidades", [])
        periodo_info = {
            "periodo": periodo.get("periodo", ""),
            "entidades": [],
            "peor_situacion": 0,
            "monto_total": 0,
        }
        for e in entidades:
            ent = {
                "entidad": e.get("entidad", ""),
                "situacion": e.get("situacion", 0),
                "monto": e.get("monto", 0),
                "dias_atraso": e.get("diasAtrasoPago", 0),
                "refinanciaciones": e.get("refinanciaciones", False),
                "situacion_juridica": e.get("situacionJuridica", False),
                "proceso_concursal": e.get("procesoConcursal", False),
                "en_revision": e.get("enRevision", False),
            }
            periodo_info["entidades"].append(ent)

        if periodo_info["entidades"]:
            periodo_info["peor_situacion"] = max(e["situacion"] for e in periodo_info["entidades"])
            periodo_info["monto_total"] = sum(e["monto"] for e in periodo_info["entidades"])

        periodos_detalle.append(periodo_info)

    ultimo = periodos_detalle[0]
    peor_situacion = ultimo["peor_situacion"]
    monto_total = ultimo["monto_total"]

    proceso_concursal = any(e["proceso_concursal"] for e in ultimo["entidades"])
    situacion_juridica = any(e["situacion_juridica"] for e in ultimo["entidades"])

    evolucion = "sin_historial"
    if len(periodos_detalle) >= 2:
        sit_actual = periodos_detalle[0]["peor_situacion"]
        sit_anterior = periodos_detalle[1]["peor_situacion"]
        if sit_actual < sit_anterior:
            evolucion = "mejorando"
        elif sit_actual > sit_anterior:
            evolucion = "empeorando"
        else:
            evolucion = "estable"

    return {
        "bcra_situacion": peor_situacion,
        "bcra_situacion_texto": SITUACION_TEXTOS.get(peor_situacion, "Desconocida"),
        "bcra_monto_total": monto_total,
        "bcra_entidades": len(ultimo["entidades"]),
        "bcra_detalle": ultimo["entidades"],
        "bcra_periodos": periodos_detalle,
        "bcra_evolucion": evolucion,
        "bcra_proceso_concursal": proceso_concursal,
        "bcra_situacion_juridica": situacion_juridica,
    }


def consultar_cheques(cuit: str) -> dict:
    """Consulta cheques rechazados con detalle completo."""
    url = f"https://api.bcra.gob.ar/centraldedeudores/v1.0/Cheques/{cuit}"
    r = _hacer_request(url)

    if r is None:
        return {"bcra_cheques_rechazados": -1, "bcra_cheques_detalle": []}

    if r.status_code == 404:
        return {"bcra_cheques_rechazados": 0, "bcra_cheques_detalle": []}

    if r.status_code != 200:
        return {"bcra_cheques_rechazados": -1, "bcra_cheques_detalle": []}

    try:
        data = r.json()
    except Exception:
        return {"bcra_cheques_rechazados": -1, "bcra_cheques_detalle": []}

    resultados = data.get("results", {})
    if not resultados:
        return {"bcra_cheques_rechazados": 0, "bcra_cheques_detalle": []}

    cheques_raw = resultados.get("cheques", [])
    causales = resultados.get("causales", [])

    cheques_detalle = []
    for ch in cheques_raw:
        cheques_detalle.append({
            "nro_cheque": ch.get("nroCheque", ""),
            "fecha_rechazo": ch.get("fechaRechazo", ""),
            "monto": ch.get("monto", 0),
            "entidad": ch.get("entidad", ""),
            "causal": ch.get("causal", ""),
            "fecha_pago": ch.get("fechaPago", ""),
            "rehabilitado": bool(ch.get("fechaPago")),
        })

    if not cheques_detalle and causales:
        total = sum(c.get("cantidad", 0) for c in causales)
        return {
            "bcra_cheques_rechazados": total,
            "bcra_cheques_detalle": causales,
        }

    total = len(cheques_detalle)
    rehabilitados = sum(1 for ch in cheques_detalle if ch["rehabilitado"])
    pendientes = total - rehabilitados

    return {
        "bcra_cheques_rechazados": total,
        "bcra_cheques_rehabilitados": rehabilitados,
        "bcra_cheques_pendientes": pendientes,
        "bcra_cheques_detalle": cheques_detalle,
    }


def enriquecer_bcra(comercio: dict) -> dict:
    """Enriquece un comercio con datos de BCRA (deudas + cheques)."""
    cuit = comercio.get("cuit", "")
    cuit_limpio = re.sub(r"[^0-9]", "", cuit)
    if not cuit_limpio or len(cuit_limpio) != 11:
        return comercio

    deudas = consultar_deudas(cuit_limpio)
    comercio.update(deudas)

    cheques = consultar_cheques(cuit_limpio)
    comercio.update(cheques)

    comercio["bcra_consultado"] = True
    comercio["deuda_bapro"] = any(
        "PROVINCIA" in d.get("entidad", "").upper()
        for d in comercio.get("bcra_detalle", [])
    )
    return comercio


def enriquecer_bcra_lote(comercios: list, callback=None) -> tuple:
    """
    Enriquece comercios con BCRA secuencial con pausa.
    2s entre consultas para evitar 429. Cache 24h.
    callback(actual, total) para progreso.
    """
    cache = _cargar_cache_bcra()

    # Separar: ya consultados / en cache / pendientes
    pendientes = []
    total_con_cuit = 0
    for c in comercios:
        cuit = c.get("cuit", "")
        cuit_limpio = re.sub(r"[^0-9]", "", cuit)
        if not cuit_limpio or len(cuit_limpio) != 11:
            continue
        total_con_cuit += 1
        if c.get("bcra_consultado"):
            continue
        # Cache hit
        if cuit_limpio in cache:
            c.update(cache[cuit_limpio])
            continue
        pendientes.append((c, cuit_limpio))

    procesados = total_con_cuit - len(pendientes)

    if callback:
        callback(procesados, total_con_cuit)

    for comercio, cuit_limpio in pendientes:
        deudas = consultar_deudas(cuit_limpio)
        time.sleep(1)
        cheques = consultar_cheques(cuit_limpio)
        comercio.update(deudas)
        comercio.update(cheques)
        comercio["bcra_consultado"] = True
        comercio["deuda_bapro"] = any(
            "PROVINCIA" in d.get("entidad", "").upper()
            for d in comercio.get("bcra_detalle", [])
        )

        # Guardar en cache
        resultado = {}
        for k, v in comercio.items():
            if k.startswith("bcra_") or k == "deuda_bapro":
                resultado[k] = v
        resultado["_fecha"] = datetime.now().isoformat()
        cache[cuit_limpio] = resultado

        procesados += 1
        if callback:
            callback(procesados, total_con_cuit)

        # Pausa entre CUITs para no triggear 429
        time.sleep(2)

        # Guardar cache cada 20 consultas
        if procesados % 20 == 0:
            _guardar_cache_bcra(cache)

    _guardar_cache_bcra(cache)

    _guardar_cache_bcra(cache)
    ok = sum(1 for c in comercios if c.get("bcra_consultado"))
    return comercios, ok
