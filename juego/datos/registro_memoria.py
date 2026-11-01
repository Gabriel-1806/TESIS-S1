"""Registro en memoria, con los mismos métodos que RegistroPartida.

Sirve para las pruebas de la capa lógica y para simular jugadores en
evaluar_prototipo, sin usar la base de datos.
"""


class RegistroEnMemoria:
    def __init__(self):
        self.rutas, self.respuestas, self.ganadas, self.completada = {}, [], set(), False

    def ruta(self, ataque):
        return self.rutas.get(ataque)

    def guardar_ruta(self, ataque, datos):
        if datos is None:
            self.rutas.pop(ataque, None)
        else:
            self.rutas[ataque] = datos

    def registrar_respuesta(self, ataque, nivel, codigo, texto, correcta):
        self.respuestas.append((ataque, nivel, codigo, correcta))

    def resumen(self, ataque=None):
        lista = [r for r in self.respuestas if ataque is None or r[0] == ataque]
        return {"respondidas": len(lista), "correctas": sum(1 for r in lista if r[3])}

    def niveles_acertados(self, ataque):
        return {r[1] for r in self.respuestas if r[0] == ataque and r[3]}

    def insignias(self):
        return set(self.ganadas)

    def asignar_insignia(self, ataque):
        self.ganadas.add(ataque)

    def marcar_completada(self):
        self.completada = True
