"""
Motor de priorización de leads.
Prioridad A/B/C/D basada en reglas simples y legibles.
Sin scoring opaco.
"""

RUBROS_ALTA_DEMANDA = {
    "Supermercado", "Ferretería", "Electrónica", "Farmacia",
    "Concesionaria", "Inmobiliaria", "Estudio contable", "Estudio jurídico",
    "Estación de servicio", "Centro comercial",
}


def calcular_prioridad(lead):
    """
    Asigna prioridad A/B/C/D con razón legible.

    A: contactable + vigente + canal claro + no duplicado
    B: contactable pero incompleto, o sin algún criterio fuerte
    C: requiere visita, o vigencia dudosa pero recuperable
    D: duplicado, sin contacto, no vigente, fuera de foco
    """
    contactable = lead.get("contact_available", False)
    vigente = lead.get("vigencia_digital") == "vigente"
    canal = lead.get("primary_channel", "")
    duplicado = lead.get("duplicate_flag", False)
    calidad = lead.get("contact_quality", "")
    requires_visit = lead.get("requires_visit", False)
    rubro = lead.get("rubro_google", "")
    distance_km = lead.get("distance_km", 99)
    reviews = lead.get("reviews_count", 0)

    # D: causas de descarte
    if duplicado:
        return "D", "Duplicado detectado"
    if not contactable and not vigente:
        return "D", "Sin contacto y sin vigencia"
    if canal == "sin_canal" and not vigente:
        return "D", "Sin canal de contacto ni vigencia"

    # A: todo en orden
    canal_claro = canal in ("whatsapp", "llamada", "mail")
    rubro_relevante = rubro in RUBROS_ALTA_DEMANDA
    cercano = distance_km <= 2

    if contactable and vigente and canal_claro and not duplicado:
        razones = ["contactable", "vigente", f"canal: {canal}"]
        if calidad == "alta":
            razones.append("contacto completo")
        if rubro_relevante:
            razones.append("rubro prioritario")
        if cercano:
            razones.append("cercano a sucursal")
        return "A", " · ".join(razones)

    # B: contactable pero algo falta
    if contactable and not duplicado:
        razones = [f"contactable vía {canal}"]
        if not vigente:
            razones.append("vigencia no confirmada")
        if calidad in ("baja", "media"):
            razones.append(f"contacto {calidad}")
        if not canal_claro:
            razones.append("canal indirecto")
        return "B", " · ".join(razones)

    # C: requiere visita o vigente pero sin contacto remoto
    if requires_visit or (vigente and not contactable):
        razones = []
        if requires_visit:
            razones.append("requiere visita")
        if vigente:
            razones.append("parece vigente")
        if reviews >= 10:
            razones.append(f"{reviews} reseñas")
        return "C", " · ".join(razones) if razones else "posible recuperación"

    # D: resto
    motivos = []
    if not contactable:
        motivos.append("sin contacto")
    if not vigente:
        motivos.append("vigencia dudosa")
    return "D", " · ".join(motivos) if motivos else "sin datos suficientes"


def priorizar_lead(lead):
    """Calcula y guarda prioridad en el lead."""
    tier, razon = calcular_prioridad(lead)
    lead["priority_tier"] = tier
    lead["priority_reason"] = razon
    return lead


def priorizar_batch(leads):
    """Prioriza una lista de leads."""
    for lead in leads:
        priorizar_lead(lead)
    # Ordenar A → B → C → D
    orden = {"A": 0, "B": 1, "C": 2, "D": 3, "": 4}
    leads.sort(key=lambda x: orden.get(x.get("priority_tier", ""), 4))
    return leads


def resumen_prioridades(leads):
    """Devuelve conteo por prioridad."""
    conteo = {"A": 0, "B": 0, "C": 0, "D": 0}
    for lead in leads:
        tier = lead.get("priority_tier", "")
        if tier in conteo:
            conteo[tier] += 1
    return conteo
