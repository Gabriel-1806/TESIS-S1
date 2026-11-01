import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import InsigniaGanada, Partida, Respuesta


@admin.action(description="Descargar las respuestas seleccionadas en CSV")
def exportar_csv(modeladmin, request, queryset):
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = 'attachment; filename="respuestas_phishtrain.csv"'
    respuesta.write("﻿")  # para que Excel lea bien las tildes
    escritor = csv.writer(respuesta)
    escritor.writerow(["partida", "ataque", "nivel", "pregunta", "respuesta elegida", "correcta", "fecha"])
    for r in queryset.select_related("partida"):
        escritor.writerow([r.partida_id, r.ataque, r.nivel, r.codigo_pregunta, r.texto_elegido,
                           1 if r.es_correcta else 0, r.fecha.strftime("%d/%m/%Y %H:%M:%S")])
    return respuesta


class RespuestaEnLinea(admin.TabularInline):
    model = Respuesta
    extra = 0
    readonly_fields = ["ataque", "nivel", "codigo_pregunta", "texto_elegido", "es_correcta", "fecha"]


class InsigniaEnLinea(admin.TabularInline):
    model = InsigniaGanada
    extra = 0
    readonly_fields = ["ataque", "fecha"]


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ["id", "iniciada", "completada"]
    readonly_fields = ["clave", "rutas", "iniciada", "actualizada", "completada"]
    inlines = [InsigniaEnLinea, RespuestaEnLinea]


@admin.register(Respuesta)
class RespuestaAdmin(admin.ModelAdmin):
    list_display = ["partida", "ataque", "nivel", "codigo_pregunta", "es_correcta", "fecha"]
    list_filter = ["ataque", "nivel", "es_correcta"]
    actions = [exportar_csv]


@admin.register(InsigniaGanada)
class InsigniaGanadaAdmin(admin.ModelAdmin):
    list_display = ["partida", "ataque", "fecha"]
    list_filter = ["ataque"]
