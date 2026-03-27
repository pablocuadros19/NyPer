"""
Enriquecimiento LICITARG para NyPer.
Dado un CUIT, busca si la empresa es proveedora del estado y agrega sus datos.
Lee directamente del parquet procesado en LICITARG — sin duplicar datos.
"""

import os
import pandas as pd

LICITARG_PARQUET = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "licitarg", "proveedores.parquet")

_cache_proveedores = None


def _cargar_proveedores():
    global _cache_proveedores
    if _cache_proveedores is not None:
        return _cache_proveedores
    if not os.path.exists(LICITARG_PARQUET):
        _cache_proveedores = {}
        return _cache_proveedores
    df = pd.read_parquet(LICITARG_PARQUET)
    _cache_proveedores = df.set_index("cuit").to_dict("index")
    return _cache_proveedores


def enriquecer_con_licitarg(lead: dict) -> dict:
    """
    Busca el CUIT del lead en la base de proveedores del estado.
    Agrega campos: es_proveedor_estado, licitarg_monto_total,
    licitarg_cantidad_adj, licitarg_organismos.
    No modifica el lead si no tiene CUIT o no está en la base.
    """
    cuit = lead.get("cuit", "")
    if not cuit or len(str(cuit)) != 11:
        lead["es_proveedor_estado"] = False
        return lead

    proveedores = _cargar_proveedores()
    datos = proveedores.get(str(cuit))

    if not datos:
        lead["es_proveedor_estado"] = False
        return lead

    monto = datos.get("monto_total", 0) or 0
    cantidad = datos.get("cantidad_adjudicaciones", 0) or 0
    organismos = datos.get("organismos", "") or ""

    lead["es_proveedor_estado"] = True
    lead["licitarg_monto_total"] = float(monto)
    lead["licitarg_cantidad_adj"] = int(cantidad)
    lead["licitarg_organismos"] = str(organismos)[:120]
    lead["licitarg_monto_fmt"] = _fmt_monto(monto)

    return lead


def enriquecer_licitarg_batch(leads: list) -> tuple[list, int]:
    """Enriquece lista completa. Retorna (leads, cantidad_matches)."""
    _cargar_proveedores()
    matches = 0
    for lead in leads:
        enriquecer_con_licitarg(lead)
        if lead.get("es_proveedor_estado"):
            matches += 1
    return leads, matches


def _fmt_monto(monto) -> str:
    try:
        v = float(monto)
    except (TypeError, ValueError):
        return ""
    if v >= 1_000_000_000:
        return f"${v/1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"
