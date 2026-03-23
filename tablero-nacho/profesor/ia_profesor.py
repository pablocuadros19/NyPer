"""
Profesor IA — usa Groq API (gratis, 14400 req/día) con Llama 3.3 70B.
"""

import re
from groq import Groq

from config import GROQ_API_KEY, MODELO_PROFESOR
from profesor.prompts import (
    SYSTEM_PROMPT,
    PROMPT_SALUDO,
    PROMPT_POST_MOVIMIENTO,
    PROMPT_PEDIR_CONSEJO,
    PROMPT_FIN_PARTIDA,
    PROMPT_RESPUESTA_CHAT,
)
from memoria.database import armar_contexto_profesor


class ProfesorIA:
    """Profesor de ajedrez personalizado con Groq API (Llama 3.3 70B)."""

    def __init__(self, jugador_id):
        self.jugador_id = jugador_id
        self.client = Groq(api_key=GROQ_API_KEY)
        self.historial_conversacion = []
        self.contexto = {}
        self.system_prompt = ""
        self._actualizar_contexto()

    def _actualizar_contexto(self):
        """Actualiza el contexto del jugador desde la DB."""
        self.contexto = armar_contexto_profesor(self.jugador_id)
        if self.contexto:
            self.system_prompt = SYSTEM_PROMPT.format(
                nombre_jugador=self.contexto["nombre"],
                nombre_profesor=self.contexto["nombre_profesor"],
                edad=self.contexto["edad"],
                nivel=self.contexto["nivel"],
                total_partidas=self.contexto["total_partidas"],
                total_victorias=self.contexto["total_victorias"],
                puntos_fuertes=self.contexto["puntos_fuertes"],
                puntos_a_mejorar=self.contexto["puntos_a_mejorar"],
                jugadas_dominadas=self.contexto["jugadas_dominadas"],
                jugadas_en_progreso=self.contexto["jugadas_en_progreso"],
                resumen_ultimas_sesiones=self.contexto["resumen_ultimas_sesiones"],
            )

    def _llamar_groq(self, mensaje_usuario):
        """Llama a Groq API y retorna la respuesta."""
        if not GROQ_API_KEY:
            return "(Profesor no disponible — falta GROQ_API_KEY en .env)"

        # Agregar mensaje del usuario al historial
        self.historial_conversacion.append({
            "role": "user",
            "content": mensaje_usuario,
        })

        # Mantener historial acotado (últimos 20 mensajes)
        mensajes = self.historial_conversacion[-20:]

        respuesta = self.client.chat.completions.create(
            model=MODELO_PROFESOR,
            messages=[
                {"role": "system", "content": self.system_prompt},
                *mensajes,
            ],
            max_tokens=300,
            temperature=0.85,
        )

        texto = respuesta.choices[0].message.content

        # Guardar respuesta en historial
        self.historial_conversacion.append({
            "role": "assistant",
            "content": texto,
        })

        return texto

    def _nombre(self):
        return self.contexto.get("nombre", "Nacho") if self.contexto else "Nacho"

    def saludar(self, contexto_extra="inicio de sesión"):
        """Saludo personalizado al iniciar sesión."""
        self._actualizar_contexto()
        prompt = PROMPT_SALUDO.format(
            nombre_jugador=self._nombre(),
            contexto_extra=contexto_extra,
        )
        return self._llamar_groq(prompt)

    def comentar_movimiento(self, fen, historial, info_movimiento):
        """Comenta después de un movimiento del jugador."""
        analisis = info_movimiento.get("analisis") or {}
        prompt = PROMPT_POST_MOVIMIENTO.format(
            nombre_jugador=self._nombre(),
            fen=fen,
            historial=historial,
            ultimo_movimiento=info_movimiento.get("notacion", ""),
            es_captura="Sí" if info_movimiento.get("captura") else "No",
            es_jaque="Sí" if info_movimiento.get("es_jaque") else "No",
            calidad=analisis.get("calidad", "buena"),
            mejor_jugada=analisis.get("mejor_jugada_alternativa", "—"),
            captura_perdida="Sí" if analisis.get("captura_perdida") else "No",
        )
        return self._llamar_groq(prompt)

    def dar_consejo(self, fen, historial, turno):
        """Da consejo cuando el jugador lo pide."""
        prompt = PROMPT_PEDIR_CONSEJO.format(
            nombre_jugador=self._nombre(),
            fen=fen,
            historial=historial,
            turno=turno,
        )
        return self._llamar_groq(prompt)

    def resumir_partida(self, fen, historial, resultado):
        """Resume la partida al terminar."""
        prompt = PROMPT_FIN_PARTIDA.format(
            fen=fen,
            historial=historial,
            resultado=resultado,
            total_movimientos=historial.count("Pablo") + historial.count("Oponente"),
        )
        respuesta = self._llamar_groq(prompt)

        # Extraer resumen interno si existe
        resumen_interno = None
        match = re.search(r"<resumen_interno>(.*?)</resumen_interno>", respuesta, re.DOTALL)
        if match:
            resumen_interno = match.group(1).strip()
            respuesta = re.sub(r"<resumen_interno>.*?</resumen_interno>", "", respuesta, flags=re.DOTALL).strip()

        return {
            "mensaje": respuesta,
            "resumen_interno": resumen_interno,
        }

    def responder_chat(self, fen, historial, mensaje):
        """Responde a un mensaje libre del jugador."""
        prompt = PROMPT_RESPUESTA_CHAT.format(
            nombre_jugador=self._nombre(),
            fen=fen,
            historial=historial,
            mensaje=mensaje,
        )
        return self._llamar_groq(prompt)

    def nueva_partida(self):
        """Limpia el historial de conversación para una nueva partida."""
        self.historial_conversacion = []
        self._actualizar_contexto()
