"""
Detección de duplicados en la base de leads.
Criterios: mismo nombre similar + misma dirección, mismo teléfono,
mismo website, o cercanía geográfica extrema.
No borra nada — marca duplicados y elige master record.
"""
import re
import unicodedata
import uuid


def _normalizar_cmp(texto):
    """Normaliza para comparación: sin acentos, minúsculas, sin caracteres especiales."""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = texto.lower()
    texto = re.sub(r"[^\w\s]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def _similitud_nombre(n1, n2):
    """Similitud simple por palabras compartidas."""
    if not n1 or not n2:
        return 0
    palabras1 = set(_normalizar_cmp(n1).split())
    palabras2 = set(_normalizar_cmp(n2).split())
    # Ignorar palabras muy cortas
    palabras1 = {p for p in palabras1 if len(p) > 2}
    palabras2 = {p for p in palabras2 if len(p) > 2}
    if not palabras1 or not palabras2:
        return 0
    comunes = palabras1 & palabras2
    return len(comunes) / max(len(palabras1), len(palabras2))


def _distancia_geo(lat1, lng1, lat2, lng2):
    """Distancia euclidiana simple en grados (suficiente para detectar duplicados cercanos)."""
    return ((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5


def es_duplicado(lead_a, lead_b, umbral_nombre=0.7, umbral_geo=0.0005):
    """
    Determina si dos leads son duplicados.
    Retorna True si se detecta duplicidad.
    """
    # Mismo place_id → duplicado exacto
    if lead_a.get("source_place_id") and lead_a["source_place_id"] == lead_b.get("source_place_id"):
        return True, "mismo place_id"

    # Mismo teléfono (no vacío)
    tel_a = lead_a.get("phone_norm", "")
    tel_b = lead_b.get("phone_norm", "")
    if tel_a and tel_b and tel_a == tel_b:
        return True, "mismo teléfono"

    # Mismo website (no vacío)
    web_a = re.sub(r"^https?://", "", lead_a.get("website", "")).rstrip("/")
    web_b = re.sub(r"^https?://", "", lead_b.get("website", "")).rstrip("/")
    if web_a and web_b and web_a == web_b:
        return True, "mismo website"

    # Cercanía geográfica extrema + nombre similar
    lat_a, lng_a = lead_a.get("lat", 0), lead_a.get("lng", 0)
    lat_b, lng_b = lead_b.get("lat", 0), lead_b.get("lng", 0)

    if lat_a and lat_b:
        dist = _distancia_geo(lat_a, lng_a, lat_b, lng_b)
        if dist < umbral_geo:
            sim_nombre = _similitud_nombre(
                lead_a.get("business_name_raw", ""),
                lead_b.get("business_name_raw", "")
            )
            if sim_nombre >= umbral_nombre:
                return True, f"misma ubicación + nombre similar ({sim_nombre:.0%})"

    return False, ""


def detectar_duplicados(leads):
    """
    Detecta duplicados en la lista de leads.
    Marca duplicate_flag, duplicate_group_id y master_record_flag.
    El master record es el que tiene más datos de contacto.
    """
    n = len(leads)
    grupos = {}  # group_id → [indices]
    asignado = {}  # index → group_id

    for i in range(n):
        if i in asignado:
            continue
        for j in range(i + 1, n):
            if j in asignado and asignado[j] != asignado.get(i):
                continue
            es_dup, razon = es_duplicado(leads[i], leads[j])
            if es_dup:
                # Asignar al mismo grupo
                group_id = asignado.get(i) or asignado.get(j) or str(uuid.uuid4())[:8]
                if i not in asignado:
                    asignado[i] = group_id
                if j not in asignado:
                    asignado[j] = group_id
                if group_id not in grupos:
                    grupos[group_id] = []
                if i not in grupos[group_id]:
                    grupos[group_id].append(i)
                if j not in grupos[group_id]:
                    grupos[group_id].append(j)

    # Marcar duplicados y elegir master record
    for group_id, indices in grupos.items():
        # Master: el que tiene más canales de contacto
        def score_contacto(idx):
            l = leads[idx]
            return sum([
                bool(l.get("phone_norm")),
                bool(l.get("email_primary")),
                bool(l.get("website")),
                bool(l.get("instagram_url")),
                bool(l.get("facebook_url")),
                l.get("reviews_count", 0) / 100,
            ])

        master_idx = max(indices, key=score_contacto)

        for idx in indices:
            leads[idx]["duplicate_flag"] = True
            leads[idx]["duplicate_group_id"] = group_id
            leads[idx]["master_record_flag"] = (idx == master_idx)

    # Los que no tienen grupo no son duplicados
    for i, lead in enumerate(leads):
        if i not in asignado:
            lead["duplicate_flag"] = False
            lead["duplicate_group_id"] = ""
            lead["master_record_flag"] = True

    total_grupos = len(grupos)
    total_duplicados = sum(len(v) for v in grupos.values())
    return leads, total_grupos, total_duplicados
