"""
Clasificador de canal de abordaje y vigencia digital.
Determina el mejor canal para contactar cada lead.
Reglas simples, explicables, sin score opaco.
"""


RUBROS_ALTA_PRIORIDAD = {
    "Supermercado", "Ferretería", "Electrónica", "Farmacia",
    "Concesionaria", "Inmobiliaria", "Estudio contable", "Estudio jurídico",
    "Constructora", "Agencia de viajes", "Centro comercial",
    "Estación de servicio", "Clínica", "Laboratorio",
}


def detectar_vigencia(lead):
    """
    Determina si el lead parece vigente.
    Retorna (vigente: bool, razon: str)
    """
    razones = []

    # Señal fuerte: business_status operativo
    status = lead.get("business_status", "")
    if status == "OPERATIONAL":
        razones.append("Google reporta activo")

    # Señal media: tiene website
    if lead.get("website"):
        razones.append("tiene website")

    # Señal media: tiene teléfono
    if lead.get("phone_norm"):
        razones.append("tiene teléfono")

    # Señal media: reseñas recientes (más de 10)
    if lead.get("reviews_count", 0) >= 10:
        razones.append(f"{lead.get('reviews_count')} reseñas")

    # Señal negativa
    if status in ("CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"):
        return False, "Google reporta cerrado"

    # Vigente si al menos 1 señal positiva
    vigente = len(razones) > 0
    razon = " + ".join(razones) if razones else "sin señales de vigencia"

    return vigente, razon


def detectar_contactabilidad(lead):
    """
    Determina si el lead es contactable y la calidad del contacto.
    Retorna (contactable: bool, calidad: str)
    """
    tiene_movil = lead.get("whatsapp_probable", False)
    tiene_tel = bool(lead.get("phone_norm", ""))
    tiene_email = bool(lead.get("email_primary", ""))
    tiene_web = bool(lead.get("website", ""))
    tiene_ig = bool(lead.get("instagram_url", ""))
    tiene_fb = bool(lead.get("facebook_url", ""))

    contactable = tiene_tel or tiene_email or tiene_web or tiene_ig or tiene_fb

    # Calidad
    puntos = sum([tiene_movil * 3, tiene_tel * 2, tiene_email * 2, tiene_web, tiene_ig, tiene_fb])

    if puntos >= 5:
        calidad = "alta"
    elif puntos >= 2:
        calidad = "media"
    elif puntos >= 1:
        calidad = "baja"
    else:
        calidad = "sin_contacto"

    return contactable, calidad


def clasificar_canal(lead):
    """
    Determina canal primario y secundario de abordaje.
    Actualiza el lead in-place.
    """
    tiene_movil = lead.get("whatsapp_probable", False)
    tiene_tel = bool(lead.get("phone_norm", ""))
    tiene_email = bool(lead.get("email_primary", ""))
    tiene_web = bool(lead.get("website", ""))
    tiene_ig = bool(lead.get("instagram_url", ""))
    tiene_fb = bool(lead.get("facebook_url", ""))
    vigente = lead.get("vigencia_digital") == "vigente"
    tiene_direccion = bool(lead.get("address_raw", ""))

    # Canal primario
    if tiene_movil:
        primario = "whatsapp"
    elif tiene_tel:
        primario = "llamada"
    elif tiene_email:
        primario = "mail"
    elif tiene_ig or tiene_fb:
        primario = "redes"
    elif vigente and tiene_direccion:
        primario = "visita"
    else:
        primario = "sin_canal"

    # Canal secundario
    secundario = ""
    if primario == "whatsapp" and tiene_email:
        secundario = "mail"
    elif primario == "whatsapp":
        secundario = "llamada"
    elif primario == "llamada" and tiene_email:
        secundario = "mail"
    elif primario == "llamada" and (tiene_ig or tiene_fb):
        secundario = "redes"
    elif primario == "mail" and (tiene_ig or tiene_fb):
        secundario = "redes"
    elif primario in ("mail", "redes") and tiene_direccion:
        secundario = "visita"

    # Requires visit
    sin_contacto_remoto = primario in ("sin_canal", "visita")
    requires_visit = sin_contacto_remoto and vigente and tiene_direccion

    lead["primary_channel"] = primario
    lead["secondary_channel"] = secundario
    lead["requires_visit"] = requires_visit

    return lead


def clasificar_vigencia(lead):
    """Calcula vigencia y la guarda en el lead."""
    vigente, razon = detectar_vigencia(lead)
    lead["vigencia_digital"] = "vigente" if vigente else "dudosa"
    lead["vigencia_reason"] = razon
    return lead


def clasificar_contactabilidad(lead):
    """Calcula contactabilidad y la guarda en el lead."""
    contactable, calidad = detectar_contactabilidad(lead)
    lead["contact_available"] = contactable
    lead["contact_quality"] = calidad
    lead["contactability_status"] = "contactable" if contactable else "sin_contacto"
    return lead


def clasificar_lead(lead):
    """Aplica todas las clasificaciones a un lead."""
    clasificar_vigencia(lead)
    clasificar_contactabilidad(lead)
    clasificar_canal(lead)
    return lead


def clasificar_batch(leads):
    """Clasifica una lista de leads."""
    for lead in leads:
        clasificar_lead(lead)
    return leads
