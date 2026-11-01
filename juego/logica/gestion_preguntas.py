"""Gestión de preguntas y respuestas (RF04).

La primera pregunta básica es la del mensaje de la bandeja. Las demás se
eligen al azar entre las que el usuario todavía no vio en ese nivel. Las
cinco opciones se mezclan cada vez.
"""
import random

from .errores import ErrorJuego


class GestionPreguntas:
    def __init__(self, contenido, azar=None):
        self.banco = contenido.preguntas
        self.por_codigo = {p["codigo"]: p for p in contenido.todas_las_preguntas()}
        self.azar = azar or random.Random()

    def pregunta(self, codigo):
        return self.por_codigo[codigo]

    def elegir(self, clave, ruta):
        """Elige la siguiente pregunta del nivel de la ruta y el orden de sus opciones."""
        nivel = ruta["nivel"]
        banco = self.banco[clave][nivel]
        vistas = set(ruta["vistas"].get(nivel, []))
        candidatas = [p for p in banco if p["codigo"] not in vistas]
        if nivel == "basico" and not vistas:
            candidatas = banco[:1]
        if not candidatas:
            # Ya vio todas las del nivel: se empieza de nuevo, pero sin repetir la última.
            vistas = set()
            candidatas = [p for p in banco if p["codigo"] != ruta.get("ultima")] or banco
        pregunta = self.azar.choice(candidatas)
        orden = list(range(len(pregunta["opciones"])))
        self.azar.shuffle(orden)
        ruta["vistas"][nivel] = sorted(vistas | {pregunta["codigo"]})
        ruta["actual"] = {"codigo": pregunta["codigo"], "orden": orden}
        ruta["etapa"] = "pregunta"
        return pregunta, orden

    def evaluar(self, pregunta, orden, elegida):
        """Devuelve (es_correcta, índice original de la elegida, posición en pantalla de la correcta)."""
        if not 0 <= elegida < len(orden):
            raise ErrorJuego("Respuesta inválida.")
        original = orden[elegida]
        return original == pregunta["indice_correcto"], original, orden.index(pregunta["indice_correcto"])
