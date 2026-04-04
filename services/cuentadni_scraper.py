"""
Cruzamiento con comercios Cuenta DNI (Banco Provincia).
Lee el CSV estático en assets/cdn/comercios_cuentadni_completo.csv
y cruza por dirección (calle + número) + proximidad geográfica.
"""

import os
import re
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
            dir_raw = _safe_str(row.get("direccion"))
            comercios.append({
                "nombre": _safe_str(row.get("empresa")).upper(),
                "direccion": dir_raw,
                "dir_numero": _extraer_numero(dir_raw),
                "dir_calle": _normalizar_calle(dir_raw),
                "localidad": _safe_str(row.get("localidad")).upper(),
                "lat": lat,
                "lng": lng,
            })

    _cache = comercios
    return _cache


def cruzar_leads_con_cuentadni(leads: list, radio_metros=80) -> tuple[int, int]:
    """
    Cruza leads con comercios Cuenta DNI.
    Match: misma dirección (calle + número) dentro de un radio de 80m.
    Retorna (total_comercios_en_base, cantidad_matches).
    """
    comercios = _cargar_comercios()
    if not comercios:
        return 0, 0

    matches = 0
    for lead in leads:
        lat_lead = lead.get("lat")
        lng_lead = lead.get("lng")
        dir_lead = (lead.get("address_raw") or lead.get("address_norm") or lead.get("direccion") or "")
        nombre_lead = (lead.get("business_name_raw") or "").upper()

        if not lat_lead or not lng_lead:
            lead.setdefault("tiene_cuenta_dni", False)
            continue

        num_lead = _extraer_numero(dir_lead)
        calle_lead = _normalizar_calle(dir_lead)

        mejor_match = None
        mejor_dist = radio_metros + 1

        for com in comercios:
            dist = _haversine(lat_lead, lng_lead, com["lat"], com["lng"])
            if dist > radio_metros:
                continue

            # Match por dirección: mismo número de calle
            match_dir = (num_lead and com["dir_numero"]
                         and num_lead == com["dir_numero"]
                         and _calles_similares(calle_lead, com["dir_calle"]))

            # Match por nombre exacto (mismo lugar, mismo nombre)
            match_nombre = _nombres_similares(nombre_lead, com["nombre"])

            if (match_dir or match_nombre) and dist < mejor_dist:
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
    return len(_cargar_comercios())


# ── Helpers ──────────────────────────────────────────────────────────────────

def _extraer_numero(direccion: str) -> str:
    """Extrae el número de la dirección. Ej: 'Av San Martín 1234' → '1234'."""
    if not direccion:
        return ""
    # Buscar secuencia de dígitos (3+ chars) que parece número de calle
    nums = re.findall(r'\b(\d{2,5})\b', direccion)
    # El número de calle suele ser el último grupo de dígitos
    return nums[-1] if nums else ""


def _normalizar_calle(direccion: str) -> str:
    """Normaliza nombre de calle para comparación."""
    if not direccion:
        return ""
    d = direccion.upper()
    # Sacar número
    d = re.sub(r'\b\d{2,5}\b', '', d)
    # Normalizar abreviaciones comunes
    d = re.sub(r'\bAV\.?\b', 'AVENIDA', d)
    d = re.sub(r'\bGRAL\.?\b', 'GENERAL', d)
    d = re.sub(r'\bPRES\.?\b', 'PRESIDENTE', d)
    d = re.sub(r'\bDR\.?\b', 'DOCTOR', d)
    d = re.sub(r'\bSTA\.?\b', 'SANTA', d)
    d = re.sub(r'\bSTO\.?\b', 'SANTO', d)
    d = re.sub(r'\bBVD\.?\b', 'BOULEVARD', d)
    d = re.sub(r'\bBLVD\.?\b', 'BOULEVARD', d)
    # Limpiar caracteres especiales y espacios múltiples
    d = re.sub(r'[^A-Z0-9 ]', '', d)
    d = re.sub(r'\s+', ' ', d).strip()
    return d


def _calles_similares(calle1: str, calle2: str) -> bool:
    """Compara dos calles normalizadas."""
    if not calle1 or not calle2:
        return False
    # Contención (una dentro de la otra)
    if calle1 in calle2 or calle2 in calle1:
        return True
    # Palabras en común (sin stopwords)
    stopwords = {"DE", "LA", "EL", "LOS", "LAS", "Y", "DEL"}
    p1 = set(calle1.split()) - stopwords
    p2 = set(calle2.split()) - stopwords
    if not p1 or not p2:
        return False
    comunes = p1 & p2
    # Al menos la mitad de la calle más corta tiene que coincidir
    return len(comunes) >= max(1, min(len(p1), len(p2)) * 0.6)


def _nombres_similares(nombre1: str, nombre2: str) -> bool:
    """Compara nombres de comercio. Exigente: 2+ palabras o contención."""
    if not nombre1 or not nombre2:
        return False
    n1_clean = re.sub(r'[^A-Z0-9 ]', '', nombre1).strip()
    n2_clean = re.sub(r'[^A-Z0-9 ]', '', nombre2).strip()
    if n1_clean in n2_clean or n2_clean in n1_clean:
        return True
    stopwords = {"DE", "LA", "EL", "LOS", "LAS", "Y", "SA", "SRL", "SAS", "SUCURSAL", "SUC"}
    n1 = set(n1_clean.split()) - stopwords
    n2 = set(n2_clean.split()) - stopwords
    if not n1 or not n2:
        return False
    comunes = n1 & n2
    min_requerido = 2 if min(len(n1), len(n2)) >= 2 else 1
    return len(comunes) >= min_requerido


def _haversine(lat1, lng1, lat2, lng2):
    if None in (lat1, lng1, lat2, lng2):
        return float("inf")
    lat1, lng1, lat2, lng2 = map(radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlng / 2) ** 2
    return 2 * asin(sqrt(a)) * 6371000


def _to_float(val):
    try:
        return float(str(val).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _safe_str(val) -> str:
    if pd.isna(val) or val is None:
        return ""
    return str(val).strip()
