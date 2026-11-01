"""Gestión de mensajes (RF02 y RF03).

Arma la bandeja con un mensaje por tipo de ataque y abre la ruta del mensaje
elegido. La ruta siempre empieza en el nivel básico, así que si el usuario
salió sin ganar la insignia vuelve a empezar.
"""
from .errores import ErrorJuego


def vista_previa(texto, largo=95):
    plano = " ".join((texto or "").split())
    return plano if len(plano) <= largo else plano[: largo - 1].rstrip() + "…"


class GestionMensajes:
    def __init__(self, contenido):
        self.ataques = {a["clave"]: a for a in contenido.ataques}

    def ataque(self, clave):
        if clave not in self.ataques:
            raise ErrorJuego("Tipo de ataque inválido.")
        return self.ataques[clave]

    def numero(self, clave):
        return list(self.ataques).index(clave) + 1

    def mensaje_bandeja(self, ataque):
        correo = ataque["correo_inicial"]
        return {
            "remitente": correo["remitente"],
            "asunto": correo["asunto"],
            "vista_previa": vista_previa(correo["cuerpo"]),
            "fecha": correo["fecha"],
            "tiene_adjunto": bool(correo["adjunto"]),
        }

    def abrir(self, clave, insignias):
        """Devuelve una ruta nueva para el ataque elegido."""
        self.ataque(clave)
        if clave in insignias:
            raise ErrorJuego("Ya ganaste la insignia de este ataque.", 409)
        return {"nivel": "basico", "etapa": "inicio", "vistas": {}, "actual": None, "ultima": ""}
