"""
Resolver de CUITs por cruce de dirección.
Usa el Registro Nacional de Sociedades (datos.jus.gob.ar) para cruzar
direcciones de Google Places con domicilios fiscales.
Fallback: CuitOnline por nombre.
"""

import os
import re
import csv
import json
import unicodedata

REGISTRO_CSV = r"C:\LICITARG\data\raw\sociedades\sociedades-ba-caba.csv"
REGISTRO_ZONA = "data/registro_zona.json"

# Localidades de la zona de cobertura
LOCALIDADES_ZONA = {
    "VILLA BALLESTER", "SAN ANDRES", "SAN ANDRÉS",
    "JOSE LEON SUAREZ", "JOSÉ LEÓN SUÁREZ", "JOSE L SUAREZ",
    "SAN MARTIN", "SAN MARTÍN", "CHILAVERT",
    "VILLA MAIPU", "VILLA MAIPÚ", "VILLA LYNCH",
    "BILLINGHURST", "LOMA HERMOSA", "VILLA ZAGALA",
    "MUNRO", "VILLA ADELINA", "CARAPACHAY",
    "CASEROS", "SANTOS LUGARES", "CIUDADELA",
    "VILLA BOSCH", "CIUDAD JARDIN", "CIUDAD JARDÍN",
    "REMEDIOS DE ESCALADA", "SARANDÍ", "SARANDI",
}

# Prefijos a limpiar de calles
PREFIJOS_CALLE = [
    "AVENIDA", "AV.", "AV ", "BOULEVARD", "BVARD", "BV.",
    "CALLE", "AUTOPISTA", "RUTA NAC", "RUTA PROV",
    "BRIGADIER GENERAL", "BRIG. GRAL.", "GENERAL", "GRAL.",
    "TENIENTE", "TTE.", "CORONEL", "CNEL.", "DOCTOR", "DR.",
    "PRESIDENTE", "PDTE.", "COMANDANTE", "CMTE.",
    "INTENDENTE", "INT.", "MONSEÑOR", "MONS.",
]

# Cache en memoria
_registro_cache = None


def _normalizar_texto(texto):
    """Quita acentos, pasa a mayúsculas, limpia espacios."""
    if not texto:
        return ""
    # Quitar acentos
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    texto = texto.upper().strip()
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def _normalizar_calle(calle):
    """Normaliza nombre de calle quitando prefijos comunes."""
    calle = _normalizar_texto(calle)
    for prefijo in PREFIJOS_CALLE:
        if calle.startswith(prefijo):
            calle = calle[len(prefijo):].strip()
    # Quitar "101" u otros números de ruta al inicio
    calle = re.sub(r'^\d+\s+', '', calle)
    # Quitar puntuación
    calle = re.sub(r'[^\w\s]', '', calle)
    calle = re.sub(r'\s+', ' ', calle).strip()
    return calle


def _extraer_calle_numero(direccion_google):
    """
    Parsea dirección de Google Places.
    'Alvear 2486, Villa Ballester' → ('ALVEAR', '2486', 'VILLA BALLESTER')
    """
    if not direccion_google:
        return "", "", ""

    partes = direccion_google.split(",")
    calle_completa = partes[0].strip()
    localidad = partes[1].strip() if len(partes) > 1 else ""

    # Extraer número: último grupo numérico en la parte de calle
    numeros = re.findall(r'\b(\d{1,5})\b', calle_completa)
    numero = numeros[-1] if numeros else ""

    # Quitar el número del final para obtener la calle
    if numero:
        calle = calle_completa[:calle_completa.rfind(numero)].strip()
    else:
        calle = calle_completa

    calle_norm = _normalizar_calle(calle)
    localidad_norm = _normalizar_texto(localidad)

    return calle_norm, numero, localidad_norm


def _cargar_registro_zona():
    """Carga o genera el registro filtrado por zona."""
    global _registro_cache
    if _registro_cache is not None:
        return _registro_cache

    # Si ya existe el archivo filtrado, cargar directo
    if os.path.exists(REGISTRO_ZONA):
        print(f"Cargando registro zona desde {REGISTRO_ZONA}...")
        with open(REGISTRO_ZONA, "r", encoding="utf-8") as f:
            _registro_cache = json.load(f)
        print(f"Registro zona: {len(_registro_cache)} sociedades únicas")
        return _registro_cache

    # Si no, procesar el CSV grande (una sola vez)
    if not os.path.exists(REGISTRO_CSV):
        print("No se encontró registro_sociedades.csv")
        _registro_cache = []
        return _registro_cache

    print("Procesando Registro Nacional de Sociedades (primera vez, puede tardar)...")
    sociedades = {}  # cuit → datos

    with open(REGISTRO_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filtrar por localidad de la zona (fiscal o legal)
            loc_fiscal = _normalizar_texto(row.get("dom_fiscal_localidad", ""))
            loc_legal = _normalizar_texto(row.get("dom_legal_localidad", ""))

            en_zona = False
            for loc_zona in LOCALIDADES_ZONA:
                loc_zona_norm = _normalizar_texto(loc_zona)
                if loc_zona_norm in loc_fiscal or loc_zona_norm in loc_legal:
                    en_zona = True
                    break

            if not en_zona:
                continue

            cuit = row.get("cuit", "").strip()
            if not cuit or len(cuit) != 11:
                continue

            # Solo guardar el primer registro por CUIT (evitar duplicados por actividad)
            if cuit in sociedades:
                continue

            calle = row.get("dom_fiscal_calle", "") or ""
            numero = row.get("dom_fiscal_numero", "") or ""

            sociedades[cuit] = {
                "cuit": cuit,
                "razon_social": row.get("razon_social", ""),
                "tipo_societario": row.get("tipo_societario", ""),
                "calle": calle.strip(),
                "numero": numero.strip(),
                "localidad": row.get("dom_fiscal_localidad", "").strip(),
                "calle_norm": _normalizar_calle(calle),
                "numero_norm": re.sub(r'[^0-9]', '', numero),
            }

    _registro_cache = list(sociedades.values())

    # Guardar para no reprocesar
    os.makedirs(os.path.dirname(REGISTRO_ZONA), exist_ok=True)
    with open(REGISTRO_ZONA, "w", encoding="utf-8") as f:
        json.dump(_registro_cache, f, ensure_ascii=False, indent=2)

    print(f"Registro zona generado: {len(_registro_cache)} sociedades únicas")
    return _registro_cache


def _construir_indice():
    """Construye índice por calle normalizada para búsqueda rápida."""
    registro = _cargar_registro_zona()
    indice = {}
    for soc in registro:
        calle = soc.get("calle_norm", "")
        if calle and len(calle) > 2:
            if calle not in indice:
                indice[calle] = []
            indice[calle].append(soc)
    return indice


# Índice global
_indice_calle = None


def buscar_por_direccion(direccion_google, nombre_comercio=""):
    """
    Busca CUIT cruzando dirección de Google Places con Registro Nacional.
    Retorna lista de candidatos ordenados por confianza.
    """
    global _indice_calle
    if _indice_calle is None:
        _indice_calle = _construir_indice()

    calle_g, numero_g, localidad_g = _extraer_calle_numero(direccion_google)

    if not calle_g:
        return []

    resultados = []

    # Buscar calle exacta
    if calle_g in _indice_calle:
        for soc in _indice_calle[calle_g]:
            score = 0.5  # base por coincidencia de calle

            # Bonus por número exacto
            if numero_g and soc["numero_norm"] == numero_g:
                score += 0.4

            # Bonus por localidad
            if localidad_g and _normalizar_texto(soc["localidad"]) in localidad_g:
                score += 0.1

            if score >= 0.8:  # solo si calle + número coinciden
                resultados.append({
                    "cuit": soc["cuit"],
                    "denominacion": soc["razon_social"],
                    "score": min(round(score, 2), 1.0),
                    "tipo": "juridica",
                    "match_tipo": "direccion",
                    "direccion_registro": f"{soc['calle']} {soc['numero']}, {soc['localidad']}",
                })

    # Si no hay match exacto de calle, buscar calles similares
    if not resultados and len(calle_g) > 3:
        for calle_idx, sociedades in _indice_calle.items():
            # La calle de Google está contenida en la del registro o viceversa
            if calle_g in calle_idx or calle_idx in calle_g:
                for soc in sociedades:
                    if numero_g and soc["numero_norm"] == numero_g:
                        resultados.append({
                            "cuit": soc["cuit"],
                            "denominacion": soc["razon_social"],
                            "score": 0.75,
                            "tipo": "juridica",
                            "match_tipo": "direccion_parcial",
                            "direccion_registro": f"{soc['calle']} {soc['numero']}, {soc['localidad']}",
                        })

    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados[:5]


def resolver_cuits_batch(comercios, callback=None):
    """
    Resuelve CUITs para una lista de comercios usando cruce por dirección.
    callback(progreso, total) para reportar progreso.
    """
    print("Cargando Registro Nacional de Sociedades (zona)...")
    _cargar_registro_zona()

    global _indice_calle
    _indice_calle = _construir_indice()
    print(f"Índice construido: {len(_indice_calle)} calles indexadas")

    total = len(comercios)
    resueltos = 0

    for i, comercio in enumerate(comercios):
        direccion = comercio.get("direccion", "")
        nombre = comercio.get("nombre", "")

        candidatos = buscar_por_direccion(direccion, nombre)

        if candidatos:
            mejor = candidatos[0]
            comercio["cuit"] = mejor["cuit"]
            comercio["cuit_denominacion"] = mejor["denominacion"]
            comercio["cuit_score"] = mejor["score"]
            comercio["cuit_tipo"] = mejor["tipo"]
            comercio["cuit_estado"] = "resuelto"
            comercio["cuit_match"] = mejor["match_tipo"]
            comercio["cuit_dir_registro"] = mejor["direccion_registro"]
            resueltos += 1
        else:
            comercio["cuit"] = ""
            comercio["cuit_denominacion"] = ""
            comercio["cuit_score"] = 0
            comercio["cuit_tipo"] = ""
            comercio["cuit_estado"] = "pendiente"
            comercio["cuit_match"] = ""

        if callback:
            callback(i + 1, total)

    return comercios, resueltos


def formatear_cuit(cuit):
    """Formatea CUIT: 30-12345678-9"""
    cuit = str(cuit)
    if len(cuit) == 11:
        return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"
    return cuit
