"""Pruebas de la lectura y validación del JSON de contenido."""
import copy
import json
import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase

from juego.datos.contenido import CONTENIDO, ErrorContenido, cargar_contenido, ruta_del_archivo, validar_contenido


class ContenidoTests(SimpleTestCase):
    def setUp(self):
        with open(ruta_del_archivo(), encoding="utf-8") as archivo:
            self.datos = json.load(archivo)

    def guardar(self, datos):
        archivo = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(datos, archivo, ensure_ascii=False)
        archivo.close()
        return archivo.name

    def test_hay_72_preguntas_con_cinco_respuestas_y_su_explicacion(self):
        self.assertEqual(validar_contenido(self.datos), [])
        preguntas = CONTENIDO.todas_las_preguntas()
        self.assertEqual(len(preguntas), 72)
        for pregunta in preguntas:
            self.assertEqual(len(pregunta["opciones"]), 5)
            self.assertTrue(all(texto.strip() for texto in pregunta["retroalimentaciones"]))

    def test_un_ataque_nuevo_se_agrega_solo_con_el_json(self):
        datos = copy.deepcopy(self.datos)
        nuevo = copy.deepcopy(datos["tipos_de_ataque"][0])
        nuevo["nombre"] = "Smishing"
        nuevo["insignia"]["nombre"] = "Guardián de mensajes de texto"
        for lista in ("preguntas_basico", "preguntas_intermedio", "preguntas_avanzado"):
            for pregunta in nuevo[lista]:
                pregunta["mensaje"]["id"] = "SM-" + pregunta["mensaje"]["id"]
        datos["tipos_de_ataque"].append(nuevo)
        contenido = cargar_contenido(self.guardar(datos))
        self.assertEqual(len(contenido.ataques), 9)
        self.assertEqual(contenido.ataques[-1]["nombre"], "Smishing")
        self.assertEqual(len(contenido.preguntas["smishing"]["avanzado"]), 3)

    def test_los_marcadores_del_cuerpo_se_cambian_por_su_texto(self):
        bec = CONTENIDO.ataque("bec")
        self.assertNotIn("#", bec["correo_inicial"]["cuerpo"])
        self.assertIn("no lo comentes con nadie del área", bec["correo_inicial"]["cuerpo"])
        self.assertEqual({m["lugar"] for m in bec["marcadores"]}, {"remitente", "frase"})
        self.assertTrue(bec["imagen_insignia"].endswith("guardian-de-pagos.svg"))
        enlaces = CONTENIDO.ataque("enlaces_falsificados")["correo_inicial"]
        self.assertEqual(enlaces["enlace"], "https://docs-google.co/login?file=planilla")

    def test_un_json_con_errores_se_rechaza_explicando_el_problema(self):
        datos = copy.deepcopy(self.datos)
        pregunta = datos["tipos_de_ataque"][0]["preguntas_basico"][0]
        pregunta["respuestas"] = pregunta["respuestas"][:4]
        msg = datos["tipos_de_ataque"][1]["preguntas_basico"][0]["mensaje"]
        msg["cuerpo"] += " #no-existe#"
        msg["indicadores"].append({"id_indicador": "suelto", "texto_indicador": "texto que no está", "retroalimentacion": "e"})
        with self.assertRaises(ErrorContenido) as error:
            cargar_contenido(self.guardar(datos))
        self.assertIn("4 respuestas", str(error.exception))
        self.assertIn("#no-existe#", str(error.exception))
        self.assertIn("no aparece en el cuerpo", str(error.exception))

    def test_el_comando_validar_contenido_acepta_el_archivo_real(self):
        salida = StringIO()
        call_command("validar_contenido", stdout=salida)
        self.assertIn("8 tipos de ataque, 72 preguntas", salida.getvalue())
