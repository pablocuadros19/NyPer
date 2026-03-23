"""
Exportador de campañas comerciales a Excel.
Genera archivos listos para accionar por canal o prioridad.
"""
from io import BytesIO
from datetime import datetime

import pandas as pd


# Columnas para export comercial operativo
COLUMNAS_EXPORT = [
    "lead_id",
    "business_name_raw",
    "rubro_operativo",
    "zona",
    "address_raw",
    "primary_channel",
    "secondary_channel",
    "phone_raw",
    "whatsapp_link",
    "whatsapp_probable",
    "email_primary",
    "website",
    "instagram_url",
    "facebook_url",
    "contact_quality",
    "vigencia_digital",
    "rating",
    "reviews_count",
    "maps_url",
    "mensaje_sugerido",
    # Datos fiscales opcionales
    "cuit",
    "legal_name",
]

RENOMBRAR_EXPORT = {
    "lead_id": "ID Lead",
    "business_name_raw": "Nombre Comercio",
    "rubro_operativo": "Rubro",
    "zona": "Zona",
    "address_raw": "Dirección",
    "primary_channel": "Canal Principal",
    "secondary_channel": "Canal Secundario",
    "phone_raw": "Teléfono",
    "whatsapp_link": "Link WhatsApp",
    "whatsapp_probable": "¿WhatsApp?",
    "email_primary": "Email",
    "website": "Website",
    "instagram_url": "Instagram",
    "facebook_url": "Facebook",
    "contact_quality": "Calidad Contacto",
    "vigencia_digital": "Vigencia",
    "rating": "Rating Google",
    "reviews_count": "Reseñas",
    "maps_url": "Link Maps",
    "mensaje_sugerido": "Mensaje Sugerido",
    "cuit": "CUIT",
    "legal_name": "Razón Social",
}

# Mensajes: centralizados en services/message_templates.py
from services.message_templates import generar_mensaje


def _generar_whatsapp_link(lead):
    """Genera link wa.me si el lead tiene teléfono móvil."""
    if not lead.get("whatsapp_probable"):
        return ""
    phone = lead.get("phone_norm", "")
    if not phone:
        return ""
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    if phone.startswith("54"):
        return f"https://wa.me/{phone}"
    if phone.startswith("11") or phone.startswith("15"):
        return f"https://wa.me/549{phone}"
    return f"https://wa.me/54{phone}"


def _mensaje_por_rubro(lead):
    """Devuelve mensaje sugerido según rubro del lead."""
    return generar_mensaje(lead, "whatsapp", "", "")["texto"]


def _enriquecer_para_export(leads):
    """Agrega campos calculados para el export."""
    for lead in leads:
        lead["whatsapp_link"] = _generar_whatsapp_link(lead)
        lead["mensaje_sugerido"] = _mensaje_por_rubro(lead)
    return leads


def _preparar_df(leads, columnas=None):
    """Construye DataFrame con columnas seleccionadas."""
    _enriquecer_para_export(leads)
    cols = columnas or COLUMNAS_EXPORT
    df = pd.DataFrame(leads)
    cols_exist = [c for c in cols if c in df.columns]
    df = df[cols_exist].copy()

    # Formatear booleanos
    for col in ["whatsapp_probable"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: "Sí" if x else "No")

    df.rename(columns=RENOMBRAR_EXPORT, inplace=True)
    return df


def exportar_excel_completo(leads):
    """Exporta todos los leads a un Excel con múltiples hojas."""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Hoja 1: Todos
        df_todos = _preparar_df(leads)
        df_todos.to_excel(writer, index=False, sheet_name="Todos los leads")

        # Hoja 2: Contactables (con teléfono, WhatsApp o email)
        leads_contactables = [l for l in leads if l.get("contact_available")]
        if leads_contactables:
            _preparar_df(leads_contactables).to_excel(writer, index=False, sheet_name="Contactables")

        # Hoja 3: Para visita
        leads_visita = [l for l in leads if l.get("requires_visit")]
        if leads_visita:
            _preparar_df(leads_visita).to_excel(writer, index=False, sheet_name="Para visita")

        # Hoja 4: WhatsApp
        leads_wa = [l for l in leads if l.get("primary_channel") == "whatsapp"]
        if leads_wa:
            _preparar_df(leads_wa).to_excel(writer, index=False, sheet_name="WhatsApp")

    output.seek(0)
    return output


def exportar_excel_canal(leads, canal):
    """Exporta leads por canal primario."""
    leads_canal = [l for l in leads if l.get("primary_channel") == canal]
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _preparar_df(leads_canal).to_excel(writer, index=False, sheet_name=f"Canal {canal}"[:28])
    output.seek(0)
    return output, len(leads_canal)


def exportar_seleccion(leads_seleccionados):
    """Exporta una selección de leads."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _preparar_df(leads_seleccionados).to_excel(writer, index=False, sheet_name="Selección")
    output.seek(0)
    return output


def nombre_archivo(prefijo="nypper"):
    return f"{prefijo}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
