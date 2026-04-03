"""
Cruzamiento con comercios Cuenta DNI (Banco Provincia).
Lee el CSV estático en assets/cdn/comercios_cuentadni_completo.csv
y cruza por proximidad geográfica + nombre contra los leads.
"""

import os
import pandas as pd
from math import radians, cos, sin, asin, sqrt

_CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "cdn", "comercios_cuentadni_completo.csv")

_cache = None


def _cargar_comercios() -> list[dict]:
    """Carga el CSV de comercios Cuenta DNI (se cachea en memoria)."""
    global _cache
    if _cache is not None:
        return _cache

    if not os.path.exists(_CSV_PATH):
        _cache = []
        return _cache

    df = pd.read_csv(_CSV_PATH, dtype=str, usecols=["empresa", "direccion", "localidad", "rubro", "latitud", "longitud"])
    comercios = []
    for _, row in df.iterrows():
        lat = _to_float(row.get("latitud"))
        lng = _to_float(row.get("longitud"))
        if lat and lng:
            comercios.append({
                "nombre": _safe_str(row.get("empresa")).upper(),
                "direccion": _safe_str(row.get("direccion")),
                "localidad": _safe_str(row.get("localidad")).upper(),
                "lat": lat,
                "lng": lng,
            })

    _cache = comercios
    return _cache


def cruzar_leads_con_cuentadni(leads: list, radio_metros=150) -> tuple[int, int]:
    """
    Cruza leads con comercios Cuenta DNI por proximidad geográfica + nombre.
    Agrega campos: tiene_cuenta_dni, cuentadni_nombre, cuentadni_distancia_m.
    Retorna (total_comercios_en_base, cantidad_matches).
    """
    comercios = _cargar_comercios()
    if not comercios:
        return 0, 0

    matches = 0
    for lead in leads:
        lat_lead = lead.get("lat")
        lng_lead = lead.get("lng")
        nombre_lead = (lead.get("nombre") or lead.get("name") or lead.get("business_name_raw") or "").upper()

        if not lat_lead or not lng_lead:
            lead.setdefault("tiene_cuenta_dni", False)
            continue

        mejor_match = None
        mejor_dist = radio_metros + 1

        for com in comercios:
            dist = _haversine(lat_lead, lng_lead, com["lat"], com["lng"])
            if dist > radio_metros:
                continue
            if _nombres_similares(nombre_lead, com["nombre"]):
                mejor_match = com
                mejor_dist = dist
                break
            elif dist < mejor_dist:
                mejor_match = com
                mejor_dist = dist

        if mejor_match:
            lead["tiene_cuenta_dni"] = True
            lead["cuentadni_nombre"] = mejor_match["nombre"]
            try:
                lead["cuentadni_distancia_m"] = int(round(mejor_dist))
            except (ValueError, OverflowError):
                lead["cuentadni_distancia_m"] = 0
            matches += 1
        else:
            lead["tiene_cuenta_dni"] = False

    return len(comercios), matches


def total_comercios() -> int:
    """Cantidad de comercios en la base."""
    return len(_cargar_comercios())


def _haversine(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return float("inf")
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371000


def _nombres_similares(nombre1: str, nombre2: str) -> bool:
    if not nombre1 or not nombre2:
        return False
    stopwords = {"DE", "LA", "EL", "LOS", "LAS", "Y", "S.A.", "SRL", "S.R.L.", "SA"}
    n1 = set(nombre1.split()) - stopwords
    n2 = set(nombre2.split()) - stopwords
    if not n1 or not n2:
        return False
    comunes = n1 & n2
    return len(comunes) >= max(1, min(len(n1), len(n2)) * 0.5)


def _to_float(val):
    try:
        return float(str(val).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _safe_str(val) -> str:
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()
