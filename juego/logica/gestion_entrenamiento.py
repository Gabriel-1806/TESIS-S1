"""Gestión del entrenamiento (RF05 y RF06).

Da la caracterización del ataque en el nivel básico, aplica las reglas de
avance y arma la retroalimentación:
  - acierto: pasa al siguiente nivel (en avanzado gana la insignia);
  - error: se explica y se da otra pregunta del mismo nivel.
"""
import re

NIVELES = ["basico", "intermedio", "avanzado"]


def sin_correcto(texto):
    """Quita el «¡Correcto!» del inicio, porque la pantalla ya dice si acertó."""
    return re.sub(r"^¡(Correcto|Exacto)!\s*", "", texto or "")


class GestionEntrenamiento:
    def __init__(self, contenido):
        self.nombres = dict(contenido.niveles)
        self.que_se_trabaja = contenido.que_se_trabaja

    def nivel(self, clave):
        return {"clave": clave, "nombre": self.nombres[clave], "indice": NIVELES.index(clave),
                "contenido": self.que_se_trabaja[clave]}

    def caracterizacion(self, ataque, numero):
        return {
            "clave": ataque["clave"], "numero": numero, "nombre": ataque["nombre"], "icono": ataque["icono"],
            "insignia": ataque["insignia"], "definicion": ataque["definicion"],
            "marcadores": ataque["marcadores"], "que_hacer": ataque["que_hacer"],
        }

    def avanzar(self, ruta, correcta, codigo):
        """Aplica la regla de avance. Devuelve (siguiente_nivel, gana_insignia)."""
        nivel = ruta["nivel"]
        if correcta and nivel == NIVELES[-1]:
            return None, True
        siguiente = NIVELES[NIVELES.index(nivel) + 1] if correcta else None
        if siguiente:
            ruta["nivel"] = siguiente
        ruta["etapa"] = "retroalimentacion"
        ruta["ultima"] = codigo
        ruta["actual"] = None
        return siguiente, False

    def retroalimentacion(self, pregunta, original):
        correcta = pregunta["indice_correcto"]
        return {
            "retro_elegida": sin_correcto(pregunta["retroalimentaciones"][original]),
            "texto_correcto": pregunta["opciones"][correcta],
            "retro_correcta": sin_correcto(pregunta["retroalimentaciones"][correcta]),
            "indicio": pregunta["indicio"],
        }
