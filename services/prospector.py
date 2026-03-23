import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

# Rubros de bajo valor bancario — se descartan
RUBROS_EXCLUIDOS = {
    "atm", "bank", "insurance_agency",
}

# Palabras clave para filtrar Banco Provincia y entidades bancarias
FILTRO_BANCO_PROVINCIA = [
    "banco provincia", "bapro", "banco de la provincia",
]

# Rubros de alto valor para prospectar
RUBROS_BUSQUEDA = [
    "store", "restaurant", "supermarket", "hardware_store",
    "electronics_store", "car_repair", "pharmacy", "veterinary_care",
    "gym", "beauty_salon", "dentist", "doctor", "lawyer",
    "accounting", "real_estate_agency", "furniture_store",
    "clothing_store", "shoe_store", "bakery", "cafe",
    "car_dealer", "gas_station", "lodging", "shopping_mall",
    "pet_store", "florist", "book_store", "jewelry_store",
    "home_goods_store", "meal_delivery", "meal_takeaway",
    "plumber", "electrician", "painter", "roofing_contractor",
    "general_contractor", "moving_company", "storage",
    "travel_agency", "insurance_agency",
    "school", "university", "hospital", "physiotherapist",
    "spa", "laundry", "car_wash", "parking",
    "campground", "night_club", "bar", "movie_theater",
    "amusement_park", "bowling_alley", "museum", "library",
    "funeral_home", "locksmith", "taxi_stand", "transit_station",
]


def _es_banco_provincia(nombre):
    """Verifica si el comercio es Banco Provincia o variante."""
    nombre_lower = nombre.lower()
    return any(filtro in nombre_lower for filtro in FILTRO_BANCO_PROVINCIA)


def _tiene_rubro_excluido(tipos):
    """Verifica si el comercio tiene un rubro excluido."""
    return any(t in RUBROS_EXCLUIDOS for t in tipos)


def _extraer_datos_basicos(place):
    """Extrae datos básicos de un resultado de Google Places."""
    return {
        "place_id": place.get("place_id", ""),
        "nombre": place.get("name", ""),
        "direccion": place.get("vicinity", ""),
        "lat": place["geometry"]["location"]["lat"],
        "lng": place["geometry"]["location"]["lng"],
        "rating": place.get("rating", 0),
        "reseñas": place.get("user_ratings_total", 0),
        "tipos": place.get("types", []),
        "rubro": _traducir_rubro(place.get("types", [])),
        "abierto": place.get("opening_hours", {}).get("open_now", None),
        "business_status": place.get("business_status", "OPERATIONAL"),
    }


def _traducir_rubro(tipos):
    """Traduce el tipo principal de Google a un rubro legible en español."""
    traducciones = {
        "store": "Comercio",
        "restaurant": "Restaurante",
        "supermarket": "Supermercado",
        "hardware_store": "Ferretería",
        "electronics_store": "Electrónica",
        "car_repair": "Taller mecánico",
        "pharmacy": "Farmacia",
        "veterinary_care": "Veterinaria",
        "gym": "Gimnasio",
        "beauty_salon": "Peluquería/Estética",
        "dentist": "Odontología",
        "doctor": "Salud",
        "lawyer": "Estudio jurídico",
        "accounting": "Estudio contable",
        "real_estate_agency": "Inmobiliaria",
        "furniture_store": "Mueblería",
        "clothing_store": "Indumentaria",
        "shoe_store": "Calzado",
        "bakery": "Panadería",
        "cafe": "Cafetería",
        "car_dealer": "Concesionaria",
        "gas_station": "Estación de servicio",
        "lodging": "Alojamiento",
        "shopping_mall": "Centro comercial",
        "pet_store": "Pet shop",
        "florist": "Florería",
        "book_store": "Librería",
        "jewelry_store": "Joyería",
        "home_goods_store": "Bazar/Hogar",
        "general_contractor": "Construcción",
        "travel_agency": "Agencia de viajes",
        "school": "Colegio/Escuela",
        "university": "Universidad",
        "hospital": "Hospital/Clínica",
        "physiotherapist": "Kinesiología",
        "spa": "Spa",
        "laundry": "Lavandería",
        "car_wash": "Lavadero de autos",
        "parking": "Estacionamiento",
        "campground": "Camping",
        "night_club": "Boliche/Bar nocturno",
        "bar": "Bar",
        "movie_theater": "Cine",
        "amusement_park": "Parque de diversiones",
        "bowling_alley": "Bowling",
        "museum": "Museo",
        "library": "Biblioteca",
        "funeral_home": "Funeraria/Cochería",
        "locksmith": "Cerrajería",
        "taxi_stand": "Remisería",
        "transit_station": "Estación de transporte",
    }
    for tipo in tipos:
        if tipo in traducciones:
            return traducciones[tipo]
    return "Otro"


def buscar_comercios(lat, lng, radio_km, min_reseñas=5, rubros_filtro=None):
    """
    Busca comercios en Google Places dentro de un radio.
    Filtra Banco Provincia y rubros de bajo valor.
    Solo devuelve comercios con mínimo de reseñas (proxy de tamaño).
    rubros_filtro: lista de types de Google Places a buscar (si None, usa todos).
    """
    radio_metros = int(radio_km * 1000)
    todos_los_comercios = []
    rubros_a_buscar = rubros_filtro if rubros_filtro else RUBROS_BUSQUEDA

    for rubro in rubros_a_buscar:
        params = {
            "location": f"{lat},{lng}",
            "radius": radio_metros,
            "type": rubro,
            "key": API_KEY,
            "language": "es",
        }

        # Primera página
        resp = requests.get(PLACES_URL, params=params)
        data = resp.json()

        if data.get("status") != "OK":
            continue

        resultados = data.get("results", [])

        # Páginas siguientes (Google Places da hasta 60 resultados en 3 páginas)
        while "next_page_token" in data:
            import time
            time.sleep(2)  # Google requiere esperar antes de pedir la siguiente página
            params_next = {
                "pagetoken": data["next_page_token"],
                "key": API_KEY,
            }
            resp = requests.get(PLACES_URL, params=params_next)
            data = resp.json()
            resultados.extend(data.get("results", []))

        for place in resultados:
            nombre = place.get("name", "")

            # Filtrar Banco Provincia
            if _es_banco_provincia(nombre):
                continue

            # Filtrar rubros excluidos
            if _tiene_rubro_excluido(place.get("types", [])):
                continue

            # Filtrar comercios cerrados permanentemente
            if place.get("business_status") == "CLOSED_PERMANENTLY":
                continue

            comercio = _extraer_datos_basicos(place)
            todos_los_comercios.append(comercio)

    # Deduplicar por place_id
    vistos = set()
    unicos = []
    for c in todos_los_comercios:
        if c["place_id"] not in vistos:
            vistos.add(c["place_id"])
            unicos.append(c)

    # Filtrar por mínimo de reseñas
    filtrados = [c for c in unicos if c["reseñas"] >= min_reseñas]

    # Ordenar por reseñas (proxy de tamaño)
    filtrados.sort(key=lambda x: x["reseñas"], reverse=True)

    return filtrados


def obtener_detalle(place_id):
    """Obtiene detalles adicionales de un comercio (teléfono, website, horarios, foto)."""
    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,international_phone_number,website,opening_hours,formatted_address,url,business_status,photos",
        "key": API_KEY,
        "language": "es",
    }
    resp = requests.get(DETAILS_URL, params=params)
    data = resp.json()

    if data.get("status") != "OK":
        return {}

    result = data.get("result", {})
    resultado = {
        "telefono": result.get("formatted_phone_number", ""),
        "telefono_intl": result.get("international_phone_number", ""),
        "website": result.get("website", ""),
        "direccion_completa": result.get("formatted_address", ""),
        "google_maps_url": result.get("url", ""),
        "horarios": result.get("opening_hours", {}).get("weekday_text", []),
        "business_status": result.get("business_status", ""),
    }
    # Foto del local (primer resultado de Google Places)
    photos = result.get("photos", [])
    if photos and API_KEY:
        ref = photos[0].get("photo_reference", "")
        if ref:
            resultado["google_photo_url"] = (
                f"https://maps.googleapis.com/maps/api/place/photo"
                f"?maxwidth=400&photo_reference={ref}&key={API_KEY}"
            )
    return resultado


def enriquecer_con_detalles(comercios, max_detalles=None):
    """Agrega detalles (teléfono, web, etc.) a una lista de comercios."""
    total = len(comercios) if max_detalles is None else min(len(comercios), max_detalles)

    for i in range(total):
        detalle = obtener_detalle(comercios[i]["place_id"])
        comercios[i].update(detalle)

    return comercios
