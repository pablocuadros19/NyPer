"""
Templates de mensajes para WhatsApp y Email.
Centraliza todos los textos de contacto comercial por familia de rubro.
"""

# ── Mapeo rubro_operativo → familia ──────────────────────────────────────────

FAMILIA_RUBRO = {
    # gastronomia
    "Restaurante": "gastronomia",
    "Cafetería": "gastronomia",
    "Panadería": "gastronomia",
    "Bar": "gastronomia",
    "Boliche/Bar nocturno": "gastronomia",
    # comercio
    "Comercio": "comercio",
    "Supermercado": "comercio",
    "Farmacia": "comercio",
    "Ferretería": "comercio",
    "Indumentaria": "comercio",
    "Electrónica": "comercio",
    "Calzado": "comercio",
    "Pet shop": "comercio",
    "Florería": "comercio",
    "Librería": "comercio",
    "Joyería": "comercio",
    "Bazar/Hogar": "comercio",
    "Mueblería": "comercio",
    "Lavandería": "comercio",
    "Lavadero de autos": "comercio",
    "Cerrajería": "comercio",
    # profesional_servicios
    "Estudio jurídico": "profesional_servicios",
    "Estudio contable": "profesional_servicios",
    "Inmobiliaria": "profesional_servicios",
    "Agencia de viajes": "profesional_servicios",
    "Peluquería/Estética": "profesional_servicios",
    "Spa": "profesional_servicios",
    "Remisería": "profesional_servicios",
    # salud_educacion_institucional
    "Odontología": "salud_educacion_institucional",
    "Salud": "salud_educacion_institucional",
    "Veterinaria": "salud_educacion_institucional",
    "Hospital/Clínica": "salud_educacion_institucional",
    "Kinesiología": "salud_educacion_institucional",
    "Museo": "salud_educacion_institucional",
    # educacion
    "Colegio/Escuela": "educacion",
    "Universidad": "educacion",
    "Biblioteca": "educacion",
    # empresa_general
    "Concesionaria": "empresa_general",
    "Estación de servicio": "empresa_general",
    "Construcción": "empresa_general",
    "Alojamiento": "empresa_general",
    "Centro comercial": "empresa_general",
    "Taller mecánico": "empresa_general",
    "Gimnasio": "empresa_general",
    "Estacionamiento": "empresa_general",
    "Camping": "empresa_general",
    "Cine": "empresa_general",
    "Parque de diversiones": "empresa_general",
    "Bowling": "empresa_general",
    "Funeraria/Cochería": "empresa_general",
    "Estación de transporte": "empresa_general",
}


# ── Templates WhatsApp ───────────────────────────────────────────────────────

WHATSAPP_TEMPLATES = {
    "generico": (
        "Hola, ¿cómo estás? Mi nombre es {nombre_usuario}, de la sucursal {sucursal_nombre}. "
        "Te escribo porque vi tu actividad y quería presentarme. "
        "Me encuentro trabajando en la vinculación y el desarrollo de actividades de la zona, "
        "y quería dejar abierto este canal por cualquier necesidad que pueda surgir. "
        "Si te interesa, seguimos por acá. Gracias."
    ),
    "comercio": (
        "Hola, ¿cómo estás? Mi nombre es {nombre_usuario}, de la sucursal {sucursal_nombre}. "
        "Te escribo porque vi tu comercio y quería ponerme en contacto. "
        "Trabajo en la vinculación y desarrollo de comercios de la zona, "
        "y quería presentarme para quedar a disposición. "
        "Si te interesa, seguimos por acá. Gracias."
    ),
    "gastronomia": (
        "Hola, ¿cómo estás? Mi nombre es {nombre_usuario}, de la sucursal {sucursal_nombre}. "
        "Te escribo porque vi tu comercio y quería acercarme. "
        "Trabajo en el acompañamiento de actividades gastronómicas de la zona, "
        "y quería presentarme y dejar abierto este canal. "
        "Si te interesa, te cuento más por acá. Gracias."
    ),
    "profesional_servicios": (
        "Hola, ¿cómo estás? Mi nombre es {nombre_usuario}, de la sucursal {sucursal_nombre}. "
        "Te escribo porque vi tu actividad y quería ponerme en contacto. "
        "Trabajo en la vinculación con actividades profesionales y de servicios de la zona, "
        "y quería presentarme para quedar a disposición. "
        "Si te interesa, seguimos por acá. Gracias."
    ),
    "salud_educacion_institucional": (
        "Hola, ¿cómo estás? Mi nombre es {nombre_usuario}, de la sucursal {sucursal_nombre}. "
        "Te escribo porque vi tu institución y quería presentarme. "
        "Trabajo en el acompañamiento a instituciones y organizaciones de la zona, "
        "y quería dejar abierto este canal de contacto. "
        "Si te interesa, con gusto seguimos por acá. Gracias."
    ),
    "educacion": (
        "Hola, ¿cómo estás? Mi nombre es {nombre_usuario}, de la sucursal {sucursal_nombre}. "
        "Te escribo porque vi tu institución y quería presentarme. "
        "Trabajo en la vinculación con instituciones educativas de la zona, "
        "acompañando distintas necesidades de la comunidad educativa. "
        "Si te interesa, con gusto seguimos por acá. Gracias."
    ),
    "empresa_general": (
        "Hola, ¿cómo estás? Mi nombre es {nombre_usuario}, de la sucursal {sucursal_nombre}. "
        "Te escribo porque vi tu comercio y quería ponerme en contacto. "
        "Trabajo en la vinculación y desarrollo de negocios de la zona, "
        "y quería presentarme para quedar a disposición. "
        "Si te interesa, seguimos por acá. Gracias."
    ),
}


# ── Templates Email ──────────────────────────────────────────────────────────

EMAIL_ASUNTOS = {
    "generico": "Contacto desde sucursal {sucursal_nombre} – {nombre_empresa}",
    "comercio": "Acompañamiento comercial para {nombre_empresa}",
    "gastronomia": "Propuesta para {nombre_empresa} desde suc. {sucursal_nombre}",
    "profesional_servicios": "Contacto profesional – suc. {sucursal_nombre}",
    "salud_educacion_institucional": "Presentación institucional – suc. {sucursal_nombre}",
    "educacion": "Presentación institucional – suc. {sucursal_nombre}",
    "empresa_general": "Contacto comercial para {nombre_empresa}",
}

EMAIL_CUERPOS = {
    "generico": (
        "Hola, buenas tardes.\n\n"
        "Mi nombre es {nombre_usuario} y me contacto desde la sucursal {sucursal_nombre} "
        "a partir de la información pública de {nombre_empresa}.\n\n"
        "Me encuentro trabajando en la vinculación y el desarrollo de actividades de la zona, "
        "por lo que quería presentarme y quedar a disposición para cualquier necesidad "
        "que pudiera surgir.\n\n"
        "Si les resulta más cómodo, con gusto puedo acercarme para conversar personalmente.\n\n"
        "Quedo a disposición para ampliarles por esta vía.\n\n"
        "Saludos,\n{nombre_usuario}"
    ),
    "comercio": (
        "Hola, buenas tardes.\n\n"
        "Mi nombre es {nombre_usuario} y me contacto desde la sucursal {sucursal_nombre} "
        "a partir de la información pública de {nombre_empresa}.\n\n"
        "Me encuentro trabajando en la vinculación y desarrollo de comercios de la zona, "
        "por lo que quería presentarme y dejar abierto este canal de contacto.\n\n"
        "Si les resulta más cómodo, con gusto puedo acercarme para conversar personalmente.\n\n"
        "Quedo a disposición para ampliarles por esta vía.\n\n"
        "Saludos,\n{nombre_usuario}"
    ),
    "gastronomia": (
        "Hola, buenas tardes.\n\n"
        "Mi nombre es {nombre_usuario} y me contacto desde la sucursal {sucursal_nombre} "
        "a partir de la información pública de {nombre_empresa}.\n\n"
        "Me encuentro trabajando en el acompañamiento de actividades gastronómicas de la zona, "
        "por lo que quería presentarme y dejar abierto este canal para futuras necesidades "
        "que pudieran tener.\n\n"
        "Si les resulta más cómodo, con gusto puedo acercarme para conversar personalmente.\n\n"
        "Quedo a disposición para ampliarles por esta vía.\n\n"
        "Saludos,\n{nombre_usuario}"
    ),
    "profesional_servicios": (
        "Hola, buenas tardes.\n\n"
        "Mi nombre es {nombre_usuario} y me contacto desde la sucursal {sucursal_nombre} "
        "a partir de la información pública de {nombre_empresa}.\n\n"
        "Me encuentro trabajando en la vinculación con actividades profesionales y de servicios "
        "de la zona, acompañando distintas necesidades según cada caso. Quería presentarme "
        "y dejar abierto este canal.\n\n"
        "Si les resulta más cómodo, con gusto puedo acercarme para conversar personalmente.\n\n"
        "Quedo a disposición para ampliarles por esta vía.\n\n"
        "Saludos,\n{nombre_usuario}"
    ),
    "salud_educacion_institucional": (
        "Hola, buenas tardes.\n\n"
        "Mi nombre es {nombre_usuario} y me contacto desde la sucursal {sucursal_nombre} "
        "a partir de la información pública de {nombre_empresa}.\n\n"
        "Me encuentro trabajando en el acompañamiento a instituciones y organizaciones de la zona, "
        "por lo que quería presentarme y dejar abierto este canal de contacto.\n\n"
        "Si les resulta más cómodo, con gusto puedo acercarme para conversar personalmente.\n\n"
        "Quedo a disposición para ampliarles por esta vía.\n\n"
        "Saludos,\n{nombre_usuario}"
    ),
    "educacion": (
        "Hola, buenas tardes.\n\n"
        "Mi nombre es {nombre_usuario} y me contacto desde la sucursal {sucursal_nombre} "
        "a partir de la información pública de {nombre_empresa}.\n\n"
        "Me encuentro trabajando en la vinculación con instituciones educativas de la zona, "
        "acompañando distintas necesidades de la comunidad educativa.\n\n"
        "Si les parece, puedo acercarme a la institución para presentarme personalmente.\n\n"
        "Quedo a disposición para ampliarles por esta vía.\n\n"
        "Saludos,\n{nombre_usuario}"
    ),
    "empresa_general": (
        "Hola, buenas tardes.\n\n"
        "Mi nombre es {nombre_usuario} y me contacto desde la sucursal {sucursal_nombre} "
        "a partir de la información pública de {nombre_empresa}.\n\n"
        "Me encuentro trabajando en la vinculación y desarrollo de negocios de la zona, "
        "por lo que quería presentarme y dejar abierto este canal para futuras necesidades "
        "que pudieran tener.\n\n"
        "Si les resulta más cómodo, con gusto puedo acercarme para conversar personalmente.\n\n"
        "Quedo a disposición para ampliarles por esta vía.\n\n"
        "Saludos,\n{nombre_usuario}"
    ),
}


# ── Función principal ────────────────────────────────────────────────────────

def _resolver_familia(rubro_operativo):
    """Devuelve la familia de template según rubro_operativo."""
    return FAMILIA_RUBRO.get(rubro_operativo, "generico")


def generar_mensaje(lead, canal, sucursal_nombre="", nombre_usuario=""):
    """
    Genera mensaje para WhatsApp o Email.

    Args:
        lead: dict del prospecto
        canal: "whatsapp" o "email"
        sucursal_nombre: nombre de la sucursal (ej: "VILLA BALLESTER")
        nombre_usuario: nombre del operador (ej: "Pablo")

    Returns:
        whatsapp: {"texto": str}
        email: {"asunto": str, "cuerpo": str}
    """
    rubro = lead.get("rubro_operativo", "")
    familia = _resolver_familia(rubro)

    # Fallbacks seguros
    nombre_empresa = lead.get("business_name_raw") or lead.get("nombre") or "su actividad"
    # Title case + sufijo institucional para sucursal
    if sucursal_nombre:
        suc = sucursal_nombre.title() + " del Banco Provincia"
    else:
        suc = "nuestra sucursal"
    usr = nombre_usuario or ""

    datos = {
        "nombre_empresa": nombre_empresa,
        "sucursal_nombre": suc,
        "nombre_usuario": usr,
    }

    if canal == "whatsapp":
        template = WHATSAPP_TEMPLATES.get(familia, WHATSAPP_TEMPLATES["generico"])
        texto = template.format(**datos)
        return {"texto": texto}

    elif canal == "email":
        # Si no hay nombre, usar fallback visible en firma
        if not usr:
            datos["nombre_usuario"] = "el equipo de la sucursal"
        asunto_tpl = EMAIL_ASUNTOS.get(familia, EMAIL_ASUNTOS["generico"])
        cuerpo_tpl = EMAIL_CUERPOS.get(familia, EMAIL_CUERPOS["generico"])
        asunto = asunto_tpl.format(**datos)
        cuerpo = cuerpo_tpl.format(**datos)
        return {"asunto": asunto, "cuerpo": cuerpo}

    return {"texto": ""}
