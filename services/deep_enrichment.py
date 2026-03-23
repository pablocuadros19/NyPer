"""
Enriquecimiento profundo: CUIT, ARCA, BCRA.
Opcional — no bloquea el flujo principal.
Aplica sobre subsets priorizados (ej: leads A y B con CUIT).
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from services.cuit_resolver import resolver_cuits_batch, formatear_cuit
from services.arca import enriquecer_arca
from services.bcra import enriquecer_bcra, consultar_deudas, consultar_cheques
from services.semaforo import clasificar_semaforo


def resolver_cuits(leads, callback=None):
    """Resuelve CUITs para todos los leads via Registro Nacional de Sociedades."""
    leads, resueltos = resolver_cuits_batch(leads, callback=callback)
    return leads, resueltos


def enriquecer_arca_subset(leads, callback=None):
    """
    Enriquece con ARCA (CuitOnline) solo los leads que tienen CUIT.
    """
    con_cuit = [l for l in leads if l.get("cuit_estado") == "resuelto" and l.get("cuit")]
    total = len(con_cuit)
    ok = 0

    for i, lead in enumerate(con_cuit):
        enriquecer_arca(lead)
        if lead.get("arca_consultado"):
            ok += 1
            lead["arca_status"] = "consultado"
            # Actualizar legal_name
            if lead.get("arca_denominacion"):
                lead["legal_name"] = lead["arca_denominacion"]
        else:
            lead["arca_status"] = "error"
        time.sleep(1)  # rate limit CuitOnline
        if callback:
            callback(i + 1, total)

    return leads, ok


def enriquecer_bcra_subset(leads, callback=None, delay=2.0):
    """
    Enriquece con BCRA solo los leads que tienen CUIT.
    Conservador: secuencial con delay para evitar 429.
    El token se toma del .env automáticamente via bcra.py.
    """
    con_cuit = [l for l in leads if l.get("cuit_estado") == "resuelto" and l.get("cuit")]
    total = len(con_cuit)
    completados = [0]

    def consultar_uno(lead):
        enriquecer_bcra(lead)
        if lead.get("bcra_consultado"):
            lead["bcra_status"] = "consultado"
        else:
            lead["bcra_status"] = "error"
        completados[0] += 1
        time.sleep(delay)
        if callback:
            callback(completados[0], total)

    # Secuencial para respetar rate limits de BCRA
    for lead in con_cuit:
        consultar_uno(lead)

    ok = sum(1 for l in con_cuit if l.get("bcra_consultado"))
    return leads, ok


def aplicar_semaforo(leads):
    """Aplica semáforo financiero (secundario) a los leads con datos BCRA/ARCA."""
    for lead in leads:
        if lead.get("arca_consultado") or lead.get("bcra_consultado"):
            clasificar_semaforo(lead)
    return leads


def enriquecer_cuit_manual(cuit_limpio):
    """
    Consulta manual de un CUIT: retorna datos ARCA + BCRA.
    Usado desde la UI para búsquedas puntuales.
    """
    import re
    from services.arca import consultar_arca
    from services.bcra import consultar_deudas, consultar_cheques

    resultado = {"cuit": cuit_limpio}

    # ARCA
    datos_arca = consultar_arca(cuit_limpio)
    resultado.update(datos_arca)

    # BCRA
    datos_deuda = consultar_deudas(cuit_limpio)
    datos_cheques = consultar_cheques(cuit_limpio)
    resultado.update(datos_deuda)
    resultado.update(datos_cheques)

    return resultado
