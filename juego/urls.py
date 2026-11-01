from django.urls import path

from . import vistas

urlpatterns = [
    path("", vistas.portada, name="portada"),
    path("juego/", vistas.juego, name="juego"),
    path("juego/reiniciar/", vistas.reiniciar, name="reiniciar"),
    path("api/estado/", vistas.api_estado, name="api_estado"),
    path("api/abrir/", vistas.api_abrir, name="api_abrir"),
    path("api/pregunta/", vistas.api_pregunta, name="api_pregunta"),
    path("api/responder/", vistas.api_responder, name="api_responder"),
]
