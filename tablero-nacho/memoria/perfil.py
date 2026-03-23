"""
Gestión de perfil del jugador — helpers para la configuración inicial.
"""

from memoria.database import crear_jugador, obtener_jugador, actualizar_jugador


def existe_perfil():
    """Verifica si ya hay un jugador configurado."""
    return obtener_jugador() is not None


def crear_perfil(nombre, edad, nombre_profesor="El Profe", sabe_jugar="aprendiendo"):
    """Crea perfil del jugador con nivel inicial según experiencia."""
    nivel = 1
    if sabe_jugar == "si":
        nivel = 2
    elif sabe_jugar == "no":
        nivel = 1

    return crear_jugador(nombre, edad, nombre_profesor, nivel)


def obtener_perfil():
    """Obtiene el perfil del jugador actual."""
    return obtener_jugador()


def actualizar_perfil(jugador_id, **campos):
    """Actualiza campos del perfil."""
    actualizar_jugador(jugador_id, **campos)
