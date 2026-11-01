"""Validación técnica del prototipo, sin participantes.

Uso: python manage.py evaluar_prototipo [--jugadores 1000] [--peticiones 200] [--semilla 7] [--salida archivo.json]

Hace tres pruebas y muestra los resultados en JSON:
  1. Validación del contenido: se meten errores a propósito en una copia del JSON
     y se revisa que el validador los encuentre.
  2. Reglas de avance: jugadores simulados recorren las 8 rutas con distintas
     probabilidades de acierto (se usa la capa lógica con un registro en memoria).
  3. Tiempo de respuesta de la API, en una base de datos temporal.
"""
import copy
import json
import random
import statistics
import time

from django.core.management.base import BaseCommand
from django.db import connection
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse

from juego.datos.contenido import CONTENIDO, ruta_del_archivo, validar_contenido
from juego.datos.registro_memoria import RegistroEnMemoria
from juego.logica.servicio import ServicioJuego


# ---------------------------------------------------------------- 1. validación del contenido
def errores_de_prueba(base):
    """Diez errores que alguien podría cometer al editar el JSON."""
    def tipo(d):
        return d["tipos_de_ataque"][0]

    def pregunta(d):
        return tipo(d)["preguntas_basico"][1]

    casos = []

    def caso(nombre, cambio):
        d = copy.deepcopy(base)
        cambio(d)
        casos.append((nombre, d))

    caso("Pregunta con 4 respuestas", lambda d: pregunta(d).update(respuestas=pregunta(d)["respuestas"][:4]))
    caso("Pregunta sin respuesta correcta", lambda d: [r.update(flag_respuesta=0) for r in pregunta(d)["respuestas"]])
    caso("Pregunta con dos respuestas correctas", lambda d: [r.update(flag_respuesta=1) for r in pregunta(d)["respuestas"][:2]])
    caso("flag_respuesta con un valor distinto de 0 o 1", lambda d: pregunta(d)["respuestas"][0].update(flag_respuesta=2))
    caso("Respuesta sin retroalimentación", lambda d: pregunta(d)["respuestas"][1].update(retroalimentacion=""))
    caso("Marcador #id# sin indicador", lambda d: pregunta(d)["mensaje"].update(cuerpo=pregunta(d)["mensaje"]["cuerpo"] + " #falta#"))
    caso("Indicador que no aparece en el mensaje", lambda d: pregunta(d)["mensaje"]["indicadores"].append(
        {"id_indicador": "suelto", "texto_indicador": "texto inexistente", "retroalimentacion": "x"}))
    caso("Nivel sin preguntas", lambda d: tipo(d).update(preguntas_avanzado=[]))
    caso("Insignia sin figura", lambda d: tipo(d)["insignia"].pop("figura"))
    caso("Mensaje con id repetido", lambda d: pregunta(d)["mensaje"].update(id=tipo(d)["preguntas_basico"][0]["mensaje"]["id"]))
    return casos


def prueba_validacion():
    with open(ruta_del_archivo(), encoding="utf-8") as archivo:
        base = json.load(archivo)
    filas = []
    for nombre, datos in errores_de_prueba(base):
        problemas = validar_contenido(datos)
        filas.append({"error": nombre, "detectado": bool(problemas), "mensaje": problemas[0] if problemas else ""})
    return {"problemas_en_el_archivo_real": len(validar_contenido(base)), "casos": filas,
            "detectados": sum(f["detectado"] for f in filas), "total": len(filas)}


# ---------------------------------------------------------------- 2. reglas de avance
def jugar(probabilidad, azar):
    """Un jugador que acierta con la probabilidad dada juega hasta ganar las 8 insignias."""
    registro = RegistroEnMemoria()
    servicio = ServicioJuego(CONTENIDO, registro, azar=azar)
    por_ruta = []
    for ataque in CONTENIDO.ataques:
        clave = ataque["clave"]
        servicio.abrir(clave)
        preguntas = 0
        while True:
            servicio.pregunta(clave)
            actual = registro.ruta(clave)["actual"]
            correcta = servicio.preguntas.pregunta(actual["codigo"])["indice_correcto"]
            posicion = actual["orden"].index(correcta)
            elegida = posicion if azar.random() < probabilidad else (posicion + 1 + azar.randrange(4)) % 5
            preguntas += 1
            if servicio.responder(clave, elegida)["insignia"]:
                break
        por_ruta.append(preguntas)
    return por_ruta, registro


def prueba_adaptabilidad(jugadores, semilla):
    azar = random.Random(semilla)
    filas = []
    for p in (0.2, 0.4, 0.6, 0.8, 1.0):
        totales, minimo, repetidas = [], [], 0
        for _ in range(jugadores):
            por_ruta, registro = jugar(p, azar)
            totales.append(sum(por_ruta))
            minimo.append(all(n == 3 for n in por_ruta))
            # Si una pregunta sale dos veces seguidas en una ruta, la regla está fallando.
            anterior = None
            for ataque, nivel, codigo, _ in registro.respuestas:
                if anterior and anterior[0] == ataque and anterior[2] == codigo:
                    repetidas += 1
                anterior = (ataque, nivel, codigo)
            assert registro.completada
        filas.append({
            "probabilidad_de_acierto": p,
            "preguntas_promedio_para_8_insignias": round(statistics.mean(totales), 1),
            "desviacion": round(statistics.pstdev(totales), 1),
            "minimo": min(totales), "maximo": max(totales),
            "preguntas_promedio_por_ruta": round(statistics.mean(totales) / len(CONTENIDO.ataques), 2),
            "esperado_teorico_por_ruta": round(3 / p, 2),
            "porcentaje_con_ruta_minima": round(100 * statistics.mean(minimo), 1),
            "preguntas_repetidas_seguidas": repetidas,
        })
    return {"jugadores_por_escenario": jugadores, "escenarios": filas}


# ---------------------------------------------------------------- 3. tiempo de respuesta
def prueba_rapidez(peticiones):
    cliente = Client()
    cliente.get(reverse("juego"))
    tiempos = {"estado": [], "abrir": [], "pregunta": [], "responder": []}
    claves = [a["clave"] for a in CONTENIDO.ataques]

    def medir(nombre, funcion):
        inicio = time.perf_counter()
        respuesta = funcion()
        tiempos[nombre].append((time.perf_counter() - inicio) * 1000)
        return respuesta

    def post(nombre_url, datos):
        return cliente.post(reverse(nombre_url), datos, content_type="application/json")

    i = 0
    while min(len(v) for v in tiempos.values()) < peticiones:
        clave = claves[i % len(claves)]
        i += 1
        medir("estado", lambda: cliente.get(reverse("api_estado")))
        if medir("abrir", lambda: post("api_abrir", {"ataque": clave})).status_code != 200:
            cliente.post(reverse("reiniciar"))
            continue
        medir("pregunta", lambda: post("api_pregunta", {"ataque": clave}))
        medir("responder", lambda: post("api_responder", {"ataque": clave, "elegida": 0}))
    filas = []
    for nombre, lista in tiempos.items():
        lista = sorted(lista[:peticiones])
        filas.append({"operacion": nombre, "peticiones": len(lista), "promedio_ms": round(statistics.mean(lista), 2),
                      "mediana_ms": round(statistics.median(lista), 2),
                      "p95_ms": round(lista[int(0.95 * len(lista)) - 1], 2), "maximo_ms": round(lista[-1], 2)})
    return {"operaciones": filas}


class Command(BaseCommand):
    help = "Validación técnica: contenido, reglas de avance y tiempo de respuesta."

    def add_arguments(self, parser):
        parser.add_argument("--jugadores", type=int, default=1000)
        parser.add_argument("--peticiones", type=int, default=200)
        parser.add_argument("--semilla", type=int, default=7)
        parser.add_argument("--salida", default="")

    def handle(self, *args, **opciones):
        resultados = {"validacion": prueba_validacion(),
                      "adaptabilidad": prueba_adaptabilidad(opciones["jugadores"], opciones["semilla"])}
        # La prueba de rapidez usa una base temporal para no tocar los datos reales.
        setup_test_environment()
        nombre_original = connection.settings_dict["NAME"]
        connection.creation.create_test_db(verbosity=0, autoclobber=True)
        try:
            resultados["rapidez"] = prueba_rapidez(opciones["peticiones"])
        finally:
            connection.creation.destroy_test_db(nombre_original, verbosity=0)
        texto = json.dumps(resultados, ensure_ascii=False, indent=2)
        if opciones["salida"]:
            with open(opciones["salida"], "w", encoding="utf-8") as archivo:
                archivo.write(texto)
        self.stdout.write(texto)
