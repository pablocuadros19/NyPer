"""
Normalización de datos de leads.
Normaliza nombres, teléfonos, direcciones, rubros.
"""
import re
import unicodedata
import uuid
from datetime import datetime


def quitar_acentos(texto):
    if not texto:
        return ""
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def normalizar_nombre(nombre):
    """Normaliza nombre comercial: sin acentos, capitalizado, sin caracteres raros."""
    if not nombre:
        return ""
    nombre = nombre.strip()
    # Capitalizar correctamente
    nombre = nombre.title()
    # Limpiar caracteres extraños
    nombre = re.sub(r"[^\w\s\-\.\,\'&]", "", nombre)
    return nombre.strip()


def normalizar_telefono(telefono):
    """
    Normaliza teléfono argentino.
    Retorna solo dígitos, eliminando país y prefijos.
    """
    if not telefono:
        return ""
    # Quitar todo lo que no sea dígito
    digitos = re.sub(r"[^\d]", "", telefono)
    # Quitar código de país +54
    if digitos.startswith("54") and len(digitos) > 10:
        digitos = digitos[2:]
    # Quitar 0 inicial de línea fija
    if digitos.startswith("0") and len(digitos) > 10:
        digitos = digitos[1:]
    return digitos


def es_movil_argentino(telefono_norm):
    """
    Detecta si el teléfono normalizado es celular argentino.
    Criterios: empieza en 11 15, o es número de 10 dígitos que empieza en 11
    seguido de un número entre 3 y 7 (rango celular GBA).
    """
    if not telefono_norm:
        return False
    t = telefono_norm
    # Formato 11X-XXXX-XXXX (10 dígitos). 114x son fijos, 113x/115x-119x son celulares
    if len(t) == 10 and t[:2] == "11" and t[2] in "356789":
        return True
    # Formato 15-XXXX-XXXX (8 dígitos, solo local)
    if len(t) == 8 and t[:2] == "15":
        return True
    return False


def normalizar_website(url):
    """Normaliza URL: asegura https://, quita trailing slash."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    url = url.rstrip("/")
    return url


def normalizar_email(email):
    """Valida y normaliza email."""
    if not email:
        return ""
    email = email.strip().lower()
    if re.match(r"^[\w\.\-]+@[\w\.\-]+\.\w{2,}$", email):
        return email
    return ""


def normalizar_direccion(direccion):
    """Normaliza dirección: capitalizada, sin dobles espacios."""
    if not direccion:
        return ""
    direccion = " ".join(direccion.split())
    return direccion.strip()


def generar_lead_id(place_id=""):
    """Genera ID único para el lead."""
    if place_id:
        # Usar place_id como base para reproducibilidad
        return f"L-{place_id[:12]}"
    return f"L-{uuid.uuid4().hex[:12]}"


def migrar_lead(lead, sucursal_lat=None, sucursal_lng=None):
    """
    Migra un lead del formato viejo al nuevo modelo de datos.
    Mantiene campos existentes y agrega los nuevos.
    """
    from utils.geo import distancia_km

    # Campos de identificación
    if "lead_id" not in lead:
        lead["lead_id"] = generar_lead_id(lead.get("place_id", ""))
    lead["source"] = lead.get("source", "google_places")
    lead["source_place_id"] = lead.get("place_id", "")
    lead["business_name_raw"] = lead.get("nombre", "")
    lead["business_name_norm"] = normalizar_nombre(lead.get("nombre", ""))
    lead["legal_name"] = lead.get("arca_denominacion", "") or lead.get("cuit_denominacion", "")
    lead["rubro_google"] = lead.get("rubro", "Otro")
    lead["rubro_operativo"] = lead.get("rubro", "Otro")

    # Segmento por CUIT o por defecto
    cuit = lead.get("cuit", "")
    if cuit and len(str(cuit)) >= 2:
        prefijo = str(cuit)[:2]
        if prefijo in ("30", "33", "34"):
            lead["segment_guess"] = "empresa"
        elif prefijo in ("20", "23", "27"):
            lead["segment_guess"] = "persona"
        else:
            lead["segment_guess"] = "sin_cuit"
    else:
        lead["segment_guess"] = "sin_cuit"

    # Ubicación
    lead["address_raw"] = lead.get("direccion", "")
    lead["address_norm"] = normalizar_direccion(lead.get("direccion_completa", "") or lead.get("direccion", ""))
    lead["maps_url"] = lead.get("google_maps_url", "")
    lead.setdefault("localidad", lead.get("zona", ""))

    if sucursal_lat and sucursal_lng:
        lat = lead.get("lat", sucursal_lat)
        lng = lead.get("lng", sucursal_lng)
        lead["distance_km"] = round(distancia_km(sucursal_lat, sucursal_lng, lat, lng), 2)
    else:
        lead.setdefault("distance_km", 0)

    # Contacto — normalizar
    tel_raw = lead.get("telefono", "")
    lead["phone_raw"] = tel_raw
    lead["phone_norm"] = normalizar_telefono(tel_raw)
    lead["phone_is_mobile_guess"] = es_movil_argentino(lead["phone_norm"])
    lead["whatsapp_probable"] = lead["phone_is_mobile_guess"]
    lead.setdefault("email_primary", "")
    lead.setdefault("email_secondary", "")
    if lead.get("website"):
        lead["website"] = normalizar_website(lead["website"])
    lead.setdefault("instagram_url", "")
    lead.setdefault("facebook_url", "")
    lead.setdefault("linkedin_url", "")

    # Señales digitales
    lead.setdefault("business_status", "OPERATIONAL" if lead.get("abierto") is not False else "UNKNOWN")
    lead.setdefault("is_open_now_guess", lead.get("abierto"))
    lead.setdefault("rating", lead.get("rating", 0))
    lead["reviews_count"] = lead.get("reseñas", lead.get("reviews_count", 0))

    # Clasificación comercial (calculada por otros módulos, inicializar)
    lead.setdefault("primary_channel", "")
    lead.setdefault("secondary_channel", "")
    lead.setdefault("requires_visit", False)
    lead.setdefault("priority_tier", "")
    lead.setdefault("priority_reason", "")
    lead.setdefault("contactability_status", "")
    lead.setdefault("contact_available", False)
    lead.setdefault("contact_quality", "")
    lead.setdefault("vigencia_digital", "")
    lead.setdefault("vigencia_reason", "")
    lead.setdefault("campaign_tag", "")

    # Auditoría
    lead.setdefault("duplicate_flag", False)
    lead.setdefault("duplicate_group_id", "")
    lead.setdefault("master_record_flag", True)
    lead.setdefault("data_confidence", "baja")
    now = datetime.now().isoformat()
    lead.setdefault("created_at", now)
    lead["updated_at"] = now
    lead.setdefault("last_verified_at", lead.get("ultima_verificacion", now))
    lead.setdefault("enrichment_stage", "discovery")
    lead.setdefault("arca_status", "consultado" if lead.get("arca_consultado") else "pendiente")
    lead.setdefault("bcra_status", "consultado" if lead.get("bcra_consultado") else "pendiente")

    return lead


def migrar_batch(leads, sucursal_lat=None, sucursal_lng=None):
    """Migra una lista de leads al nuevo modelo."""
    return [migrar_lead(lead, sucursal_lat, sucursal_lng) for lead in leads]
