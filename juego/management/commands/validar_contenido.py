"""Revisa el JSON de contenido antes de usarlo.

Uso: python manage.py validar_contenido [ruta_del_json]
"""
import json
from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from juego.datos.contenido import NIVELES_JSON, ruta_del_archivo, validar_contenido


class Command(BaseCommand):
    help = "Valida el JSON de contenido (ataques, mensajes, indicadores, preguntas, respuestas e insignias)."

    def add_arguments(self, parser):
        parser.add_argument("ruta", nargs="?", default=str(ruta_del_archivo()))

    def handle(self, *args, **opciones):
        try:
            with open(opciones["ruta"], encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, json.JSONDecodeError) as error:
            raise CommandError(f"No se pudo leer el archivo: {error}")
        problemas = validar_contenido(datos)
        if problemas:
            raise CommandError("El contenido tiene problemas:\n- " + "\n- ".join(problemas))
        tipos = datos["tipos_de_ataque"]
        por_nivel = Counter()
        marcadores = 0
        for tipo in tipos:
            for lista in NIVELES_JSON:
                por_nivel[lista] += len(tipo[lista])
                marcadores += sum(1 for p in tipo[lista] for ind in p["mensaje"]["indicadores"] if ind.get("retroalimentacion"))
        self.stdout.write(self.style.SUCCESS(
            f"Contenido válido: {len(tipos)} tipos de ataque, {sum(por_nivel.values())} preguntas "
            f"(básico {por_nivel['preguntas_basico']}, intermedio {por_nivel['preguntas_intermedio']}, "
            f"avanzado {por_nivel['preguntas_avanzado']}), {marcadores} indicadores y {len(tipos)} insignias."
        ))
