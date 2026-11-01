"""Pruebas del juego completo a través de las páginas y la API."""
import json

from django.test import TestCase
from django.urls import reverse

from juego.datos.contenido import CONTENIDO
from juego.models import InsigniaGanada, Partida, Respuesta
from juego.vistas import CLAVE_SESION

CLAVES = [a["clave"] for a in CONTENIDO.ataques]


class JuegoWebTests(TestCase):
    def setUp(self):
        self.client.get(reverse("juego"))

    def post(self, nombre, datos):
        return self.client.post(reverse(nombre), data=json.dumps(datos), content_type="application/json")

    def partida(self):
        return Partida.objects.get(id=self.client.session[CLAVE_SESION])

    def responder(self, ataque, bien=True):
        actual = self.partida().rutas[ataque]["actual"]
        correcta = CONTENIDO.preguntas[ataque][self.partida().rutas[ataque]["nivel"]]
        indice = next(p["indice_correcto"] for p in correcta if p["codigo"] == actual["codigo"])
        posicion = actual["orden"].index(indice)
        return self.post("api_responder", {"ataque": ataque, "elegida": posicion if bien else (posicion + 1) % 5})

    def test_portada_tiene_boton_para_iniciar_y_no_pide_registro(self):
        respuesta = self.client.get(reverse("portada"))
        self.assertContains(respuesta, "Aprende a identificar ataques phishing")
        self.assertContains(respuesta, reverse("juego"))
        self.assertNotContains(respuesta, "consentimiento")

    def test_bandeja_tiene_un_mensaje_por_tipo_de_ataque(self):
        estado = self.client.get(reverse("api_estado")).json()["estado"]
        self.assertEqual([a["clave"] for a in estado["ataques"]], CLAVES)
        self.assertEqual(estado["insignias"], 0)
        self.assertFalse(estado["completado"])

    def test_nivel_basico_empieza_con_la_caracterizacion(self):
        datos = self.post("api_abrir", {"ataque": "bec"}).json()
        self.assertEqual(datos["nivel"]["clave"], "basico")
        self.assertTrue(datos["ataque"]["definicion"])
        self.assertGreaterEqual(len(datos["ataque"]["marcadores"]), 3)
        pregunta = self.post("api_pregunta", {"ataque": "bec"}).json()["pregunta"]
        self.assertEqual(pregunta["codigo"], "BEC-B1")

    def test_ruta_completa_da_la_insignia_y_saca_el_mensaje(self):
        ataque = "quishing"
        self.post("api_abrir", {"ataque": ataque})
        for nivel in ["basico", "intermedio", "avanzado"]:
            pregunta = self.post("api_pregunta", {"ataque": ataque}).json()["pregunta"]
            self.assertEqual(pregunta["nivel"]["clave"], nivel)
            self.assertEqual(len(pregunta["opciones"]), 5)
            resultado = self.responder(ataque).json()
            self.assertTrue(resultado["correcta"])
            self.assertTrue(resultado["retro_elegida"])
        self.assertEqual(resultado["insignia"]["ataque"], ataque)
        self.assertTrue(InsigniaGanada.objects.filter(partida=self.partida(), ataque=ataque).exists())
        self.assertNotIn(ataque, self.partida().rutas)
        estado = self.client.get(reverse("api_estado")).json()["estado"]
        self.assertTrue(next(a for a in estado["ataques"] if a["clave"] == ataque)["ganada"])
        self.assertEqual(self.post("api_abrir", {"ataque": ataque}).status_code, 409)

    def test_respuesta_incorrecta_explica_y_da_otra_pregunta_del_mismo_nivel(self):
        ataque = "spear_phishing"
        self.post("api_abrir", {"ataque": ataque})
        primera = self.post("api_pregunta", {"ataque": ataque}).json()["pregunta"]
        resultado = self.responder(ataque, bien=False).json()
        self.assertFalse(resultado["correcta"])
        self.assertTrue(resultado["retro_correcta"])
        self.assertIsNone(resultado["siguiente_nivel"])
        segunda = self.post("api_pregunta", {"ataque": ataque}).json()["pregunta"]
        self.assertEqual(segunda["nivel"]["clave"], "basico")
        self.assertNotEqual(segunda["codigo"], primera["codigo"])

    def test_las_preguntas_no_se_repiten_seguidas(self):
        ataque = "bec"
        self.post("api_abrir", {"ataque": ataque})
        codigos = []
        for _ in range(5):
            codigos.append(self.post("api_pregunta", {"ataque": ataque}).json()["pregunta"]["codigo"])
            self.responder(ataque, bien=False)
        self.assertEqual(set(codigos[:3]), {p["codigo"] for p in CONTENIDO.preguntas[ataque]["basico"]})
        self.assertTrue(all(a != b for a, b in zip(codigos, codigos[1:])))

    def test_volver_a_abrir_el_mensaje_reinicia_en_basico(self):
        ataque = "phishing_correo"
        self.post("api_abrir", {"ataque": ataque})
        self.post("api_pregunta", {"ataque": ataque})
        self.responder(ataque)
        self.assertEqual(self.partida().rutas[ataque]["nivel"], "intermedio")
        self.post("api_abrir", {"ataque": ataque})
        pregunta = self.post("api_pregunta", {"ataque": ataque}).json()["pregunta"]
        self.assertEqual(pregunta["nivel"]["clave"], "basico")

    def test_recargar_da_la_misma_pregunta_y_la_respuesta_se_guarda_una_vez(self):
        ataque = "clone_phishing"
        self.post("api_abrir", {"ataque": ataque})
        primera = self.post("api_pregunta", {"ataque": ataque}).json()["pregunta"]
        otra_vez = self.post("api_pregunta", {"ataque": ataque}).json()["pregunta"]
        self.assertEqual(primera, otra_vez)
        self.responder(ataque)
        self.assertEqual(self.post("api_responder", {"ataque": ataque, "elegida": 0}).status_code, 409)
        self.assertEqual(Respuesta.objects.filter(partida=self.partida()).count(), 1)

    def test_progreso_muestra_nivel_alcanzado_y_contadores(self):
        ataque = "adjuntos_maliciosos"
        self.post("api_abrir", {"ataque": ataque})
        self.post("api_pregunta", {"ataque": ataque})
        self.responder(ataque, bien=False)
        self.post("api_pregunta", {"ataque": ataque})
        self.responder(ataque)
        estado = self.client.get(reverse("api_estado")).json()["estado"]
        item = next(a for a in estado["ataques"] if a["clave"] == ataque)
        self.assertEqual(item["nivel_alcanzado"], "intermedio")
        self.assertEqual((item["respondidas"], item["correctas"]), (2, 1))
        self.assertEqual((estado["respondidas"], estado["correctas"], estado["insignias"]), (2, 1, 0))

    def test_ganar_las_8_insignias_completa_el_entrenamiento(self):
        for ataque in CLAVES:
            self.post("api_abrir", {"ataque": ataque})
            for _ in range(3):
                self.post("api_pregunta", {"ataque": ataque})
                self.responder(ataque)
        estado = self.client.get(reverse("api_estado")).json()["estado"]
        self.assertEqual(estado["insignias"], 8)
        self.assertTrue(estado["completado"])
        self.assertIsNotNone(self.partida().completada)

    def test_datos_invalidos_devuelven_error(self):
        self.assertEqual(self.post("api_abrir", {"ataque": "no_existe"}).status_code, 400)
        self.assertEqual(self.post("api_responder", {"ataque": "bec", "elegida": "x"}).status_code, 400)

    def test_empezar_de_nuevo_crea_otra_partida(self):
        anterior = self.partida().id
        self.client.post(reverse("reiniciar"))
        self.assertNotEqual(self.partida().id, anterior)
