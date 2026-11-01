"""Pruebas de la capa lógica sin web ni base de datos.

El servicio se usa con un registro en memoria, igual que lo haría otra
interfaz (por ejemplo, una app móvil).
"""
import random
from unittest import TestCase

from juego.datos.contenido import CONTENIDO
from juego.datos.registro_memoria import RegistroEnMemoria
from juego.logica.errores import ErrorJuego
from juego.logica.servicio import ServicioJuego


class ServicioJuegoTests(TestCase):
    def setUp(self):
        self.registro = RegistroEnMemoria()
        self.servicio = ServicioJuego(CONTENIDO, self.registro, azar=random.Random(7))

    def responder(self, clave, bien=True):
        pregunta = self.servicio.pregunta(clave)
        orden = self.registro.ruta(clave)["actual"]["orden"]
        posicion = orden.index(self.servicio.preguntas.pregunta(pregunta["codigo"])["indice_correcto"])
        return self.servicio.responder(clave, posicion if bien else (posicion + 1) % 5)

    def test_ruta_completa_da_la_insignia(self):
        self.servicio.abrir("quishing")
        for nivel in ["basico", "intermedio", "avanzado"]:
            resultado = self.responder("quishing")
            self.assertEqual(resultado["nivel"]["clave"], nivel)
        self.assertEqual(resultado["insignia"]["ataque"], "quishing")
        self.assertIn("quishing", self.registro.insignias())
        self.assertIsNone(self.registro.ruta("quishing"))

    def test_error_mantiene_el_nivel_y_cambia_la_pregunta(self):
        self.servicio.abrir("bec")
        primera = self.servicio.pregunta("bec")["codigo"]
        resultado = self.responder("bec", bien=False)
        self.assertFalse(resultado["correcta"])
        self.assertIsNone(resultado["siguiente_nivel"])
        self.assertNotEqual(self.servicio.pregunta("bec")["codigo"], primera)

    def test_primera_pregunta_basica_es_la_del_mensaje_de_la_bandeja(self):
        self.servicio.abrir("spear_phishing")
        self.assertEqual(self.servicio.pregunta("spear_phishing")["codigo"], "SP-B1")

    def test_errores_de_la_capa_logica(self):
        with self.assertRaises(ErrorJuego):
            self.servicio.abrir("no_existe")
        with self.assertRaises(ErrorJuego) as error:
            self.servicio.pregunta("bec")
        self.assertEqual(error.exception.codigo, 409)

    def test_todas_las_insignias_completan_el_entrenamiento(self):
        for ataque in CONTENIDO.ataques:
            self.servicio.abrir(ataque["clave"])
            for _ in range(3):
                self.responder(ataque["clave"])
        self.assertTrue(self.registro.completada)
        self.assertTrue(self.servicio.estado()["completado"])
