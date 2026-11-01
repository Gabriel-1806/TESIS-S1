"""Gestión del progreso y de las insignias (RF07 y RF08).

Calcula lo que se muestra en Mi progreso y Mis insignias y asigna la
insignia cuando se acierta la pregunta del nivel avanzado.
"""


class GestionProgreso:
    def __init__(self, contenido, mensajes):
        self.contenido = contenido
        self.mensajes = mensajes

    def nivel_alcanzado(self, registro, clave, insignias):
        if clave in insignias:
            return "insignia"
        acertados = registro.niveles_acertados(clave)
        if "intermedio" in acertados:
            return "avanzado"
        if "basico" in acertados:
            return "intermedio"
        return "basico" if registro.resumen(clave)["respondidas"] else ""

    def estado(self, registro):
        insignias = registro.insignias()
        ataques = []
        for numero, ataque in enumerate(self.contenido.ataques, start=1):
            clave = ataque["clave"]
            resumen = registro.resumen(clave)
            ataques.append({
                "clave": clave, "numero": numero, "nombre": ataque["nombre"], "icono": ataque["icono"],
                "insignia": ataque["insignia"], "imagen_insignia": ataque["imagen_insignia"],
                "ganada": clave in insignias,
                "nivel_alcanzado": self.nivel_alcanzado(registro, clave, insignias),
                "respondidas": resumen["respondidas"],
                "correctas": resumen["correctas"],
                **self.mensajes.mensaje_bandeja(ataque),
            })
        total = len(self.contenido.ataques)
        general = registro.resumen()
        return {
            "ataques": ataques,
            "insignias": len(insignias),
            "total": total,
            "completado": len(insignias) >= total,
            "respondidas": general["respondidas"],
            "correctas": general["correctas"],
            "niveles": [{"clave": c, "nombre": n, "contenido": self.contenido.que_se_trabaja[c]}
                        for c, n in self.contenido.niveles],
        }

    def asignar_insignia(self, registro, ataque):
        """Asigna la insignia y, si ya tiene todas, marca la partida como completada."""
        registro.asignar_insignia(ataque["clave"])
        if len(registro.insignias()) >= len(self.contenido.ataques):
            registro.marcar_completada()
        return {"ataque": ataque["clave"], "nombre": ataque["insignia"], "icono": ataque["icono"],
                "imagen": ataque["imagen_insignia"], "nombre_ataque": ataque["nombre"]}
