"""
Enriquecimiento de contacto para leads.
Funciona SIN CUIT — aplica sobre todo el universo de leads.
Busca: teléfono, website, email, redes sociales.
"""
import re
import time
import logging
import requests
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from bs4 import BeautifulSoup

from services.prospector import obtener_detalle


# Patrones para extraer redes sociales de websites/texto
PATRON_INSTAGRAM = re.compile(
    r"(?:instagram\.com/|@)([\w\.]+)", re.IGNORECASE
)
PATRON_FACEBOOK = re.compile(
    r"facebook\.com/([\w\.\-]+)", re.IGNORECASE
)
PATRON_LINKEDIN = re.compile(
    r"linkedin\.com/(?:company|in)/([\w\-]+)", re.IGNORECASE
)
PATRON_EMAIL = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)
# Links de WhatsApp en HTML
PATRON_WHATSAPP = re.compile(
    r"(?:wa\.me/|api\.whatsapp\.com/send\?phone=|whatsapp\.com/send\?phone=)(\d+)", re.IGNORECASE
)
# Teléfonos argentinos (fijos y móviles)
PATRON_TELEFONO_AR = re.compile(
    r"(?:\+?54[\s\-]?)?(?:9[\s\-]?)?(?:11|[2-9]\d{1,3})[\s\-]?\d{4}[\s\-]?\d{4}"
)

# Palabras clave para encontrar páginas de contacto
_PAGINAS_CONTACTO = [
    "contacto", "contact", "contactenos", "contactanos",
    "nosotros", "about", "quienes-somos", "quien-somos",
    "empresa", "info", "informacion",
]

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "es-AR,es;q=0.9",
}

# Filtros de emails basura
_EMAILS_BASURA = {"sentry", "example", "ejemplo", "test", "noreply", "no-reply",
                  "wixpress", "placeholder", "yourdomain", "tudominio", "wordpress"}
_EXTENSIONES_ARCHIVO = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf", ".js", ".css")
_DOMINIOS_GENERICOS = {"mail.com", "correo.com", "email.com"}


def _es_email_valido(email):
    """Filtra emails falsos (placeholders, archivos, genéricos)."""
    e = email.lower()
    if any(palabra in e for palabra in _EMAILS_BASURA):
        return False
    if any(e.endswith(ext) for ext in _EXTENSIONES_ARCHIVO):
        return False
    dominio = e.split("@")[-1] if "@" in e else ""
    if dominio in _DOMINIOS_GENERICOS:
        return False
    return True


def _extraer_emails_inteligente(html):
    """Extrae emails del HTML con múltiples estrategias, priorizando los más confiables."""
    import json as _json
    emails = []
    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    # Capa 1: mailto links (más confiable)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().startswith("mailto:"):
            email = href[7:].split("?")[0].strip()
            if email and _es_email_valido(email):
                emails.append(email)

    # Capa 2: JSON-LD / schema.org
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = _json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    e = item.get("email", "")
                    if e and _es_email_valido(e):
                        emails.append(e)
        except Exception:
            pass

    # Capa 3: Texto visible solamente (fallback)
    if not emails:
        for tag in soup(["script", "style"]):
            tag.decompose()
        texto_visible = soup.get_text(separator=" ")
        encontrados = PATRON_EMAIL.findall(texto_visible)
        emails.extend(e for e in encontrados if _es_email_valido(e))

    # Deduplicar preservando orden
    vistos = set()
    unicos = []
    for e in emails:
        e_lower = e.lower()
        if e_lower not in vistos:
            vistos.add(e_lower)
            unicos.append(e)

    return unicos


def _extraer_sociales_de_texto(texto):
    """Extrae URLs de redes sociales de un texto HTML o plano."""
    resultado = {}
    if not texto:
        return resultado

    m_ig = PATRON_INSTAGRAM.search(texto)
    if m_ig:
        usuario = m_ig.group(1)
        # Ignorar handles genéricos
        if usuario.lower() not in ("p", "share", "sharer", "intent"):
            resultado["instagram_url"] = f"https://www.instagram.com/{usuario}"

    m_fb = PATRON_FACEBOOK.search(texto)
    if m_fb:
        usuario = m_fb.group(1)
        if usuario.lower() not in ("share", "sharer", "dialog", "plugins"):
            resultado["facebook_url"] = f"https://www.facebook.com/{usuario}"

    m_li = PATRON_LINKEDIN.search(texto)
    if m_li:
        resultado["linkedin_url"] = f"https://www.linkedin.com/company/{m_li.group(1)}"

    m_wa = PATRON_WHATSAPP.search(texto)
    if m_wa:
        resultado["whatsapp_link"] = f"https://wa.me/{m_wa.group(1)}"
        resultado["whatsapp_phone"] = m_wa.group(1)

    emails_validos = _extraer_emails_inteligente(texto)
    if emails_validos:
        resultado["email_primary"] = emails_validos[0]
        if len(emails_validos) > 1:
            resultado["email_secondary"] = emails_validos[1]

    return resultado


def _scrapear_website(url, timeout=8):
    """Intenta scrapear el website para extraer emails y redes sociales."""
    if not url:
        return {}
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "es-AR,es;q=0.9",
        }
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return _extraer_sociales_de_texto(r.text)
    except Exception:
        pass
    return {}


def enriquecer_contacto(lead, log=True):
    """
    Enriquece un lead con datos de contacto.
    Funciona sin CUIT.
    1. Consulta Google Places Details (teléfono, website, url del mapa)
    2. Si tiene website, lo scrapea buscando email y redes
    """
    import logging
    logger = logging.getLogger("nypper")

    place_id = lead.get("source_place_id") or lead.get("place_id", "")
    nombre = lead.get("business_name_raw", lead.get("nombre", "?"))
    if log:
        logger.info(f"Enriqueciendo: {nombre}")

    # Solo consultar Google Places si no tiene teléfono todavía
    if place_id and not lead.get("phone_norm"):
        detalle = obtener_detalle(place_id)
        # Preferir teléfono internacional (+54...) para mejor normalización
        tel_raw = detalle.get("telefono_intl") or detalle.get("telefono")
        if tel_raw:
            lead["telefono"] = detalle.get("telefono", tel_raw)
            from services.normalizer import normalizar_telefono, es_movil_argentino
            lead["phone_raw"] = tel_raw
            lead["phone_norm"] = normalizar_telefono(tel_raw)
            lead["phone_is_mobile_guess"] = es_movil_argentino(lead["phone_norm"])
            lead["whatsapp_probable"] = lead["phone_is_mobile_guess"]
        if detalle.get("website") and not lead.get("website"):
            from services.normalizer import normalizar_website
            lead["website"] = normalizar_website(detalle["website"])
        if detalle.get("google_maps_url") and not lead.get("maps_url"):
            lead["maps_url"] = detalle["google_maps_url"]
        if detalle.get("direccion_completa") and not lead.get("address_norm"):
            lead["address_norm"] = detalle["direccion_completa"]

    # Scrapear website si tiene y le faltan redes/email/whatsapp
    tiene_redes = lead.get("instagram_url") or lead.get("facebook_url")
    tiene_email = lead.get("email_primary")
    tiene_wa = lead.get("whatsapp_probable")
    if lead.get("website") and (not tiene_redes or not tiene_email or not tiene_wa):
        sociales = _scrapear_website(lead["website"])
        # Procesar WhatsApp encontrado
        wa_phone = sociales.pop("whatsapp_phone", None)
        wa_link = sociales.pop("whatsapp_link", None)
        if wa_phone and not lead.get("whatsapp_probable"):
            from services.normalizer import normalizar_telefono, es_movil_argentino
            phone_norm = normalizar_telefono(wa_phone)
            if phone_norm:
                if not lead.get("phone_norm"):
                    # No tenía teléfono → usar como principal
                    lead["phone_raw"] = wa_phone
                    lead["phone_norm"] = phone_norm
                    lead["phone_is_mobile_guess"] = es_movil_argentino(phone_norm)
                else:
                    # Ya tenía fijo → guardar como secundario
                    lead["phone_secondary"] = phone_norm
                lead["whatsapp_probable"] = True
                lead["whatsapp_link"] = wa_link or f"https://wa.me/{phone_norm}"
        # Resto de datos (redes, email) sin pisar existentes
        for campo, valor in sociales.items():
            if valor and not lead.get(campo):
                lead[campo] = valor

    lead["enrichment_stage"] = "contacto"
    return lead


def _buscar_links_contacto(html, base_url):
    """Busca links internos a páginas de contacto/about en el HTML."""
    dominio_base = urlparse(base_url).netloc
    encontrados = []
    try:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:"):
                continue
            url_completa = urljoin(base_url, href)
            # Solo mismo dominio
            if urlparse(url_completa).netloc != dominio_base:
                continue
            href_lower = href.lower()
            texto_lower = (a.get_text() or "").lower()
            if any(kw in href_lower or kw in texto_lower for kw in _PAGINAS_CONTACTO):
                if url_completa not in encontrados:
                    encontrados.append(url_completa)
                    if len(encontrados) >= 3:
                        break
    except Exception:
        pass
    return encontrados


def _extraer_telefonos_de_texto(texto):
    """Extrae teléfonos argentinos de un texto."""
    if not texto:
        return []
    matches = PATRON_TELEFONO_AR.findall(texto)
    # Limpiar: solo dígitos, mínimo 8 dígitos
    limpios = []
    for m in matches:
        digitos = re.sub(r"\D", "", m)
        if len(digitos) >= 8:
            limpios.append(digitos)
    return limpios


def rastrear_website_profundo(lead):
    """
    Scraping profundo del website del lead.
    Busca páginas internas de contacto/about para extraer más emails,
    teléfonos y redes sociales. No pisa datos existentes.
    """
    logger = logging.getLogger("nypper")
    website = lead.get("website", "")
    if not website:
        return lead

    nombre = lead.get("business_name_raw", lead.get("nombre", "?"))
    logger.info(f"Rastreando website: {nombre} — {website}")

    todos_los_datos = {}
    telefonos_encontrados = []

    try:
        # 1. Scrapear página principal
        r = requests.get(website, headers=_HEADERS, timeout=8, allow_redirects=True)
        if r.status_code != 200:
            return lead

        html_principal = r.text
        datos_principal = _extraer_sociales_de_texto(html_principal)
        todos_los_datos.update(datos_principal)
        telefonos_encontrados.extend(_extraer_telefonos_de_texto(html_principal))

        # 2. Buscar y scrapear páginas internas de contacto
        links = _buscar_links_contacto(html_principal, website)
        for link in links:
            try:
                r2 = requests.get(link, headers=_HEADERS, timeout=8, allow_redirects=True)
                if r2.status_code == 200:
                    datos_pagina = _extraer_sociales_de_texto(r2.text)
                    # No pisar datos ya encontrados
                    for campo, valor in datos_pagina.items():
                        if valor and campo not in todos_los_datos:
                            todos_los_datos[campo] = valor
                    telefonos_encontrados.extend(_extraer_telefonos_de_texto(r2.text))
            except Exception:
                continue

    except Exception:
        return lead

    # 3. Procesar WhatsApp encontrado
    wa_phone = todos_los_datos.pop("whatsapp_phone", None)
    wa_link = todos_los_datos.pop("whatsapp_link", None)
    if wa_phone and not lead.get("whatsapp_probable"):
        from services.normalizer import normalizar_telefono, es_movil_argentino
        phone_norm = normalizar_telefono(wa_phone)
        if phone_norm:
            if not lead.get("phone_norm"):
                lead["phone_raw"] = wa_phone
                lead["phone_norm"] = phone_norm
                lead["phone_is_mobile_guess"] = es_movil_argentino(phone_norm)
            else:
                lead["phone_secondary"] = phone_norm
            lead["whatsapp_probable"] = True
            lead["whatsapp_link"] = wa_link or f"https://wa.me/{phone_norm}"

    # 4. Aplicar datos al lead sin pisar lo existente
    for campo, valor in todos_los_datos.items():
        if valor and not lead.get(campo):
            lead[campo] = valor

    # 5. Si no tiene teléfono, intentar con los encontrados por regex
    if not lead.get("phone_norm") and telefonos_encontrados:
        from services.normalizer import normalizar_telefono, es_movil_argentino
        tel_raw = telefonos_encontrados[0]
        phone_norm = normalizar_telefono(tel_raw)
        if phone_norm and len(phone_norm) >= 10:
            lead["phone_raw"] = tel_raw
            lead["phone_norm"] = phone_norm
            lead["phone_is_mobile_guess"] = es_movil_argentino(phone_norm)
            lead["whatsapp_probable"] = lead["phone_is_mobile_guess"]
    # Si tiene fijo pero no WhatsApp, buscar móvil en teléfonos encontrados
    elif lead.get("phone_norm") and not lead.get("whatsapp_probable") and telefonos_encontrados:
        from services.normalizer import normalizar_telefono, es_movil_argentino
        for tel in telefonos_encontrados:
            phone_norm = normalizar_telefono(tel)
            if phone_norm and es_movil_argentino(phone_norm):
                lead["phone_secondary"] = phone_norm
                lead["whatsapp_probable"] = True
                lead["whatsapp_link"] = f"https://wa.me/54{phone_norm}"
                break

    lead["website_rastreado"] = True
    return lead


def rastrear_websites_batch(leads, callback=None):
    """
    Rastreo profundo de websites para leads que tienen website
    pero les faltan datos de contacto.
    """
    candidatos = [
        l for l in leads
        if l.get("website")
        and not l.get("website_rastreado")
    ]
    total = len(candidatos)
    for idx, lead in enumerate(candidatos):
        rastrear_website_profundo(lead)
        if callback:
            callback(idx + 1, total)
    return leads, total


def enriquecer_contacto_batch(leads, max_workers=5, callback=None):
    """
    Enriquece contacto de todos los leads en paralelo.
    NO requiere CUIT — aplica sobre el universo completo.
    """
    total = len(leads)
    completados = [0]

    def enriquecer_uno(lead):
        result = enriquecer_contacto(lead)
        completados[0] += 1
        if callback:
            callback(completados[0], total)
        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(enriquecer_uno, lead): i for i, lead in enumerate(leads)}
        for future in as_completed(futures):
            try:
                future.result(timeout=30)
            except Exception:
                pass

    return leads
