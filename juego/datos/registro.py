"""Registro de la partida en la base de datos (rutas, respuestas e insignias).

La capa lógica solo usa los métodos de esta clase; no sabe que hay modelos de Django.
"""
from django.utils import timezone

from ..models import InsigniaGanada, Respuesta


class RegistroPartida:
    def __init__(self, partida):
        self.partida = partida

    def ruta(self, ataque):
        return (self.partida.rutas or {}).get(ataque)

    def guardar_ruta(self, ataque, datos):
        """Guarda la ruta de un ataque. Con datos=None la borra."""
        rutas = dict(self.partida.rutas or {})
        if datos is None:
            rutas.pop(ataque, None)
        else:
            rutas[ataque] = datos
        self.partida.rutas = rutas
        self.partida.save(update_fields=["rutas", "actualizada"])

    def registrar_respuesta(self, ataque, nivel, codigo, texto, correcta):
        Respuesta.objects.create(partida=self.partida, ataque=ataque, nivel=nivel, codigo_pregunta=codigo,
                                 texto_elegido=texto[:300], es_correcta=correcta)

    def resumen(self, ataque=None):
        consulta = self.partida.respuestas.all()
        if ataque:
            consulta = consulta.filter(ataque=ataque)
        return {"respondidas": consulta.count(), "correctas": consulta.filter(es_correcta=True).count()}

    def niveles_acertados(self, ataque):
        return set(self.partida.respuestas.filter(ataque=ataque, es_correcta=True).values_list("nivel", flat=True))

    def insignias(self):
        return set(self.partida.insignias.values_list("ataque", flat=True))

    def asignar_insignia(self, ataque):
        InsigniaGanada.objects.get_or_create(partida=self.partida, ataque=ataque)

    def marcar_completada(self):
        if not self.partida.completada:
            self.partida.completada = timezone.now()
            self.partida.save(update_fields=["completada"])
