"""Servicio del juego: lo único de la capa lógica que usa la presentación.

Tiene cuatro operaciones (estado, abrir, pregunta y responder), coordina
los módulos de gestión y guarda el avance con el registro de la capa de datos.
"""
from .errores import ErrorJuego
from .gestion_entrenamiento import GestionEntrenamiento
from .gestion_mensajes import GestionMensajes
from .gestion_preguntas import GestionPreguntas
from .gestion_progreso import GestionProgreso


class ServicioJuego:
    def __init__(self, contenido, registro, azar=None):
        self.registro = registro
        self.mensajes = GestionMensajes(contenido)
        self.preguntas = GestionPreguntas(contenido, azar)
        self.entrenamiento = GestionEntrenamiento(contenido)
        self.progreso = GestionProgreso(contenido, self.mensajes)

    def estado(self):
        return self.progreso.estado(self.registro)

    def abrir(self, clave):
        """Abre el mensaje de un ataque y empieza su ruta en el nivel básico."""
        ruta = self.mensajes.abrir(clave, self.registro.insignias())
        self.registro.guardar_ruta(clave, ruta)
        ataque = self.mensajes.ataque(clave)
        return {
            "ataque": self.entrenamiento.caracterizacion(ataque, self.mensajes.numero(clave)),
            "correo": ataque["correo_inicial"],
            "nivel": self.entrenamiento.nivel("basico"),
        }

    def _para_mostrar(self, clave, nivel, pregunta, orden):
        return {
            "ataque": clave,
            "codigo": pregunta["codigo"],
            "nivel": self.entrenamiento.nivel(nivel),
            "correo": pregunta["correo"],
            "enunciado": pregunta["enunciado"],
            "opciones": [pregunta["opciones"][i] for i in orden],
        }

    def pregunta(self, clave):
        self.mensajes.ataque(clave)
        ruta = self.registro.ruta(clave)
        if not ruta:
            raise ErrorJuego("Abre primero el mensaje desde la bandeja.", 409)
        actual = ruta.get("actual")
        if ruta["etapa"] == "pregunta" and actual:
            # Si recarga la página o hace doble clic, se devuelve la misma pregunta.
            return self._para_mostrar(clave, ruta["nivel"], self.preguntas.pregunta(actual["codigo"]), actual["orden"])
        pregunta, orden = self.preguntas.elegir(clave, ruta)
        self.registro.guardar_ruta(clave, ruta)
        return self._para_mostrar(clave, ruta["nivel"], pregunta, orden)

    def responder(self, clave, elegida):
        ataque = self.mensajes.ataque(clave)
        ruta = self.registro.ruta(clave)
        if not ruta or ruta["etapa"] != "pregunta" or not ruta.get("actual"):
            raise ErrorJuego("Esta pregunta ya fue respondida.", 409)
        actual = ruta["actual"]
        pregunta = self.preguntas.pregunta(actual["codigo"])
        correcta, original, posicion_correcta = self.preguntas.evaluar(pregunta, actual["orden"], elegida)
        nivel = ruta["nivel"]
        self.registro.registrar_respuesta(clave, nivel, pregunta["codigo"], pregunta["opciones"][original], correcta)

        siguiente, gana = self.entrenamiento.avanzar(ruta, correcta, pregunta["codigo"])
        insignia = None
        if gana:
            insignia = self.progreso.asignar_insignia(self.registro, ataque)
            self.registro.guardar_ruta(clave, None)
        else:
            self.registro.guardar_ruta(clave, ruta)
        return {
            "correcta": correcta,
            "elegida": elegida,
            "posicion_correcta": posicion_correcta,
            **self.entrenamiento.retroalimentacion(pregunta, original),
            "nivel": self.entrenamiento.nivel(nivel),
            "siguiente_nivel": self.entrenamiento.nivel(siguiente) if siguiente else None,
            "insignia": insignia,
            "estado": self.estado(),
        }
