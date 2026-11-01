"""Vistas web del juego (capa de presentación).

Aquí no hay reglas del juego: cada vista busca la partida del usuario,
llama al servicio de la capa lógica y devuelve la respuesta en JSON.
"""
import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.views.decorators.http import require_GET, require_POST

from .datos.contenido import CONTENIDO
from .datos.registro import RegistroPartida
from .logica.errores import ErrorJuego
from .logica.servicio import ServicioJuego
from .models import Partida

CLAVE_SESION = "phishtrain_partida"


def partida_actual(request, crear=False):
    partida_id = request.session.get(CLAVE_SESION)
    partida = Partida.objects.filter(id=partida_id).first() if partida_id else None
    if partida is None and crear:
        partida = Partida.objects.create()
        request.session[CLAVE_SESION] = partida.id
    return partida


def leer_json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}


def con_urls_de_imagenes(datos):
    """Cambia la ruta de cada figura de insignia por su dirección web."""
    for ataque in (datos.get("estado") or datos).get("ataques", []):
        ataque["imagen_insignia"] = static(ataque["imagen_insignia"])
    if datos.get("insignia"):
        datos["insignia"]["imagen"] = static(datos["insignia"]["imagen"])
    return datos


def ejecutar(request, accion, *argumentos):
    """Ejecuta una operación del servicio con la partida bloqueada y responde en JSON."""
    try:
        with transaction.atomic():
            partida = Partida.objects.select_for_update().get(id=partida_actual(request, crear=True).id)
            datos = accion(ServicioJuego(CONTENIDO, RegistroPartida(partida)), *argumentos)
    except ErrorJuego as error:
        return JsonResponse({"ok": False, "mensaje": error.mensaje}, status=error.codigo)
    return JsonResponse({"ok": True, **con_urls_de_imagenes(datos)})


# ---------------------------------------------------------------- páginas
@require_GET
def portada(request):
    partida = partida_actual(request)
    empezada = bool(partida and (partida.respuestas.exists() or partida.rutas))
    return render(request, "portada.html", {
        "empezada": empezada,
        "insignias": partida.insignias.count() if partida else 0,
        "total_ataques": len(CONTENIDO.ataques),
    })


@require_GET
def juego(request):
    partida_actual(request, crear=True)
    return render(request, "juego.html", {"total_ataques": len(CONTENIDO.ataques)})


@require_POST
def reiniciar(request):
    request.session.pop(CLAVE_SESION, None)
    partida_actual(request, crear=True)
    return redirect("juego")


# ---------------------------------------------------------------- API
@require_GET
def api_estado(request):
    return ejecutar(request, lambda servicio: {"estado": servicio.estado()})


@require_POST
def api_abrir(request):
    return ejecutar(request, ServicioJuego.abrir, leer_json(request).get("ataque"))


@require_POST
def api_pregunta(request):
    return ejecutar(request, lambda servicio, clave: {"pregunta": servicio.pregunta(clave)},
                    leer_json(request).get("ataque"))


@require_POST
def api_responder(request):
    datos = leer_json(request)
    try:
        elegida = int(datos.get("elegida"))
    except (TypeError, ValueError):
        return JsonResponse({"ok": False, "mensaje": "Respuesta inválida."}, status=400)
    return ejecutar(request, ServicioJuego.responder, datos.get("ataque"), elegida)
