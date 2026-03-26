import math


def distancia_km(lat1, lng1, lat2, lng2):
    """Calcula distancia en km entre dos coordenadas (Haversine)."""
    R = 6371  # Radio de la Tierra en km

    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def clasificar_zona(lat, lng):
    """
    Clasifica la zona aproximada según coordenadas.
    Zonas de la sucursal 5155: Villa Ballester, San Andrés, J.L. Suárez, Chilavert.
    """
    zonas = {
        "Villa Ballester": (-34.5525, -58.5564),
        "San Andrés": (-34.5430, -58.5280),
        "José León Suárez": (-34.5220, -58.5630),
        "Chilavert": (-34.5640, -58.5370),
    }

    zona_cercana = None
    min_dist = float("inf")

    for nombre, (z_lat, z_lng) in zonas.items():
        dist = distancia_km(lat, lng, z_lat, z_lng)
        if dist < min_dist:
            min_dist = dist
            zona_cercana = nombre

    return zona_cercana


def zona_desde_direccion(direccion, lat=None, lng=None):
    """
    Extrae la localidad/zona desde el campo vicinity de Google Places.
    El vicinity viene como "Calle 123, Localidad" — el último componente es la zona.
    Fallback a clasificar_zona si no hay dirección útil.
    """
    if direccion:
        partes = [p.strip() for p in direccion.split(",") if p.strip()]
        if len(partes) >= 2:
            return partes[-1]
        elif len(partes) == 1:
            return partes[0]
    # fallback solo para 5155 / coordenadas conocidas
    if lat is not None and lng is not None:
        return clasificar_zona(lat, lng)
    return ""
