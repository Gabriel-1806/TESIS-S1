"""Lectura y validación del archivo JSON con el contenido del juego.

Es el único módulo que conoce el formato del JSON. La estructura es la que
se definió con el asesor:

  tipo de ataque: nombre, descripcion, preguntas_basico, preguntas_intermedio,
                  preguntas_avanzado, insignia
  pregunta:       mensaje, enunciado, respuestas (5)
  mensaje:        id, remitente, destinatario, fecha, asunto, cuerpo, adjunto, indicadores
  indicador:      id_indicador, texto_indicador, retroalimentacion (y enlace si es un enlace)
  respuesta:      flag_respuesta (1 correcta, 0 incorrecta), texto_respuesta, retroalimentacion
  insignia:       nombre, descripcion, figura

En el cuerpo, cada marcador se escribe como #id_indicador# y se cambia por su
texto_indicador. Si el indicador es el correo del remitente o el nombre del
adjunto, no se escribe en el cuerpo. Un enlace sin retroalimentación es solo
el enlace del mensaje y no se explica como marcador.
"""
import json
import re
import unicodedata
from pathlib import Path

from django.conf import settings

CARPETA_INSIGNIAS = "img/insignias/"
RESPUESTAS_POR_PREGUNTA = 5

# Nombre de cada lista de preguntas en el JSON y el nivel que le corresponde.
NIVELES_JSON = {"preguntas_basico": "basico", "preguntas_intermedio": "intermedio", "preguntas_avanzado": "avanzado"}
NIVELES = [("basico", "Básico"), ("intermedio", "Intermedio"), ("avanzado", "Avanzado")]
QUE_SE_TRABAJA = {
    "basico": "Reconocer qué es el ataque y sus marcadores más visibles en un mensaje claro.",
    "intermedio": "Detectar los marcadores en mensajes más creíbles y elegir la acción segura.",
    "avanzado": "Analizar mensajes muy realistas, donde los marcadores son sutiles o se combinan.",
}
ICONOS = {"phishing por correo": "🎣", "spear phishing": "🎯", "business email compromise (bec)": "💼",
          "clone phishing": "🧬", "adjuntos maliciosos": "📎", "enlaces a sitios falsificados": "🔗",
          "quishing": "📱", "correos escritos con inteligencia artificial": "🤖"}
# Clave corta de los ocho ataques (es la que se guarda en la base de datos).
# Si se agrega un ataque nuevo al JSON, su clave sale de su nombre.
CLAVES = {"phishing por correo": "phishing_correo", "spear phishing": "spear_phishing",
          "business email compromise (bec)": "bec", "clone phishing": "clone_phishing",
          "adjuntos maliciosos": "adjuntos_maliciosos", "enlaces a sitios falsificados": "enlaces_falsificados",
          "quishing": "quishing", "correos escritos con inteligencia artificial": "ia_generado"}
MARCADOR = re.compile(r"#([^#\s]+)#")
SEPARADOR_QUE_HACER = " Qué hacer: "


class ErrorContenido(ValueError):
    """El JSON no tiene la estructura que espera el juego."""


def clave_ataque(nombre):
    if nombre.lower() in CLAVES:
        return CLAVES[nombre.lower()]
    plano = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", plano).strip("_")


def lugar_del_indicador(mensaje, indicador):
    """Dónde está el indicador: en una frase del cuerpo, el enlace, el remitente o el adjunto."""
    if indicador.get("enlace"):
        return "enlace"
    if f"#{indicador.get('id_indicador')}#" in (mensaje.get("cuerpo") or ""):
        return "frase"
    if indicador.get("texto_indicador") == (mensaje.get("remitente") or {}).get("correo"):
        return "remitente"
    if indicador.get("texto_indicador") == (mensaje.get("adjunto") or {}).get("nombre_archivo"):
        return "adjunto"
    return None


def validar_contenido(datos):
    """Revisa el JSON y devuelve una lista con los problemas (vacía si todo está bien)."""
    problemas = []
    ids_vistos = set()
    tipos = datos.get("tipos_de_ataque") or []
    if not tipos:
        problemas.append("No hay ningún tipo de ataque en «tipos_de_ataque».")

    def revisar_mensaje(msg, donde):
        for campo in ("id", "remitente", "destinatario", "asunto", "cuerpo"):
            if not msg.get(campo):
                problemas.append(f"{donde}: falta «{campo}» en el mensaje.")
        if not (msg.get("remitente") or {}).get("correo"):
            problemas.append(f"{donde}: el remitente necesita nombre y correo.")
        indicadores = msg.get("indicadores") or []
        ids = [ind.get("id_indicador") for ind in indicadores]
        for marca in MARCADOR.findall(msg.get("cuerpo") or ""):
            if marca not in ids:
                problemas.append(f"{donde}: el cuerpo usa #{marca}#, pero no hay un indicador con ese id.")
        if len(set(ids)) != len(ids):
            problemas.append(f"{donde}: hay indicadores con el mismo id.")
        if len([ind for ind in indicadores if ind.get("enlace")]) > 1:
            problemas.append(f"{donde}: el mensaje tiene más de un enlace.")
        for ind in indicadores:
            iid = ind.get("id_indicador")
            if not ind.get("texto_indicador"):
                problemas.append(f"{donde}: el indicador {iid} no tiene texto_indicador.")
            if not ind.get("retroalimentacion") and not ind.get("enlace"):
                problemas.append(f"{donde}: el indicador {iid} no tiene retroalimentación.")
            lugar = lugar_del_indicador(msg, ind)
            if lugar is None:
                problemas.append(f"{donde}: el indicador {iid} no aparece en el cuerpo ni coincide con el remitente o el adjunto.")
            elif lugar == "enlace" and f"#{iid}#" not in msg.get("cuerpo", ""):
                problemas.append(f"{donde}: el enlace {iid} debe escribirse en el cuerpo como #{iid}#.")

    for tipo in tipos:
        nombre = tipo.get("nombre") or "?"
        clave = clave_ataque(nombre)
        if clave in ids_vistos:
            problemas.append(f"Tipo de ataque repetido: {nombre}.")
        ids_vistos.add(clave)
        for campo in ("nombre", "descripcion", "insignia"):
            if not tipo.get(campo):
                problemas.append(f"{nombre}: falta «{campo}».")
        insignia = tipo.get("insignia") or {}
        if not insignia.get("nombre") or not (insignia.get("figura") or {}).get("nombre_archivo"):
            problemas.append(f"{nombre}: la insignia necesita nombre y figura.")
        for lista in NIVELES_JSON:
            preguntas = tipo.get(lista) or []
            if not preguntas:
                problemas.append(f"{nombre}/{lista}: no tiene preguntas.")
            for pregunta in preguntas:
                msg = pregunta.get("mensaje") or {}
                pid = msg.get("id", "?")
                if pid in ids_vistos:
                    problemas.append(f"Identificador de mensaje repetido: {pid}.")
                ids_vistos.add(pid)
                if msg:
                    revisar_mensaje(msg, pid)
                else:
                    problemas.append(f"{nombre}/{lista}: hay una pregunta sin mensaje.")
                if not pregunta.get("enunciado"):
                    problemas.append(f"{pid}: falta el enunciado.")
                respuestas = pregunta.get("respuestas") or []
                if len(respuestas) != RESPUESTAS_POR_PREGUNTA:
                    problemas.append(f"{pid}: tiene {len(respuestas)} respuestas y se piden {RESPUESTAS_POR_PREGUNTA}.")
                if any(r.get("flag_respuesta") not in (0, 1) or isinstance(r.get("flag_respuesta"), bool) for r in respuestas):
                    problemas.append(f"{pid}: flag_respuesta debe ser 1 (correcta) o 0 (incorrecta).")
                if sum(1 for r in respuestas if r.get("flag_respuesta") == 1) != 1:
                    problemas.append(f"{pid}: debe tener exactamente una respuesta correcta.")
                if any(not r.get("texto_respuesta") or not r.get("retroalimentacion") for r in respuestas):
                    problemas.append(f"{pid}: hay respuestas sin texto o sin retroalimentación.")
        primero = (tipo.get("preguntas_basico") or [{}])[0].get("mensaje") or {}
        if primero and not [ind for ind in primero.get("indicadores") or [] if ind.get("retroalimentacion")]:
            problemas.append(f"{nombre}: el mensaje de la primera pregunta básica necesita marcadores para caracterizar el ataque.")
    return problemas


def armar_correo(msg):
    """Convierte un mensaje del JSON en el correo que se muestra en pantalla."""
    indicadores = {ind["id_indicador"]: ind for ind in msg.get("indicadores") or []}
    enlace = next((ind for ind in indicadores.values() if ind.get("enlace")), None)

    def reemplazar(marca):
        ind = indicadores[marca.group(1)]
        return "" if ind.get("enlace") else ind["texto_indicador"]

    return {
        "remitente": msg["remitente"]["nombre"],
        "correo_remitente": msg["remitente"]["correo"],
        "destinatario": (msg.get("destinatario") or {}).get("nombre", ""),
        "fecha": msg.get("fecha") or "Hoy",
        "asunto": msg["asunto"],
        "cuerpo": MARCADOR.sub(reemplazar, msg["cuerpo"]).rstrip(),
        "texto_enlace": enlace["texto_indicador"] if enlace else "",
        "enlace": enlace["enlace"] if enlace else "",
        "adjunto": (msg.get("adjunto") or {}).get("nombre_archivo", ""),
    }


def armar_marcadores(msg):
    """Indicadores que tienen retroalimentación, listos para el área de entrenamiento."""
    marcadores = []
    for ind in msg.get("indicadores") or []:
        if not ind.get("retroalimentacion"):
            continue
        titulo, _, texto = ind["retroalimentacion"].partition(". ")
        lugar = lugar_del_indicador(msg, ind)
        marcadores.append({"titulo": titulo, "texto": texto or titulo, "lugar": lugar,
                           "frase": ind["texto_indicador"] if lugar == "frase" else ""})
    return marcadores


def indicio_clave(msg):
    """Primer marcador del mensaje; se resalta en verde al mostrar la respuesta."""
    for marcador in armar_marcadores(msg):
        return marcador["frase"] or marcador["lugar"]
    return ""


class Contenido:
    """Contenido del JSON ya validado y ordenado como lo usa la capa lógica."""

    def __init__(self, datos):
        problemas = validar_contenido(datos)
        if problemas:
            raise ErrorContenido("El archivo de contenido tiene problemas:\n- " + "\n- ".join(problemas))
        self.datos = datos
        self.niveles = NIVELES
        self.que_se_trabaja = QUE_SE_TRABAJA
        self.ataques = []
        self.preguntas = {}  # {clave del ataque: {nivel: [preguntas]}}
        for tipo in datos["tipos_de_ataque"]:
            clave = clave_ataque(tipo["nombre"])
            definicion, _, que_hacer = tipo["descripcion"].partition(SEPARADOR_QUE_HACER)
            inicial = tipo["preguntas_basico"][0]["mensaje"]
            insignia = tipo["insignia"]
            self.ataques.append({
                "clave": clave,
                "nombre": tipo["nombre"],
                "icono": ICONOS.get(tipo["nombre"].lower(), "✉"),
                "insignia": insignia["nombre"],
                "descripcion_insignia": insignia.get("descripcion", ""),
                "imagen_insignia": CARPETA_INSIGNIAS + insignia["figura"]["nombre_archivo"],
                "definicion": definicion,
                "que_hacer": que_hacer,
                "correo_inicial": armar_correo(inicial),
                "marcadores": armar_marcadores(inicial),
            })
            self.preguntas[clave] = {
                nivel: [{
                    "codigo": p["mensaje"]["id"],
                    "correo": armar_correo(p["mensaje"]),
                    "enunciado": p["enunciado"],
                    "opciones": [r["texto_respuesta"] for r in p["respuestas"]],
                    "retroalimentaciones": [r["retroalimentacion"] for r in p["respuestas"]],
                    "indice_correcto": next(i for i, r in enumerate(p["respuestas"]) if r["flag_respuesta"] == 1),
                    "indicio": indicio_clave(p["mensaje"]),
                } for p in tipo[lista]]
                for lista, nivel in NIVELES_JSON.items()
            }

    def ataque(self, clave):
        return next((a for a in self.ataques if a["clave"] == clave), None)

    def todas_las_preguntas(self):
        return [p for niveles in self.preguntas.values() for lista in niveles.values() for p in lista]


def ruta_del_archivo():
    return Path(settings.ARCHIVO_CONTENIDO)


def cargar_contenido(ruta=None):
    with open(ruta or ruta_del_archivo(), encoding="utf-8") as archivo:
        return Contenido(json.load(archivo))


# El contenido se carga una sola vez, al iniciar el servidor.
CONTENIDO = cargar_contenido()
