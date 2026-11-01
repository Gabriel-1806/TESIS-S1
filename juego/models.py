import uuid

from django.db import models


class Nivel(models.TextChoices):
    BASICO = "basico", "Básico"
    INTERMEDIO = "intermedio", "Intermedio"
    AVANZADO = "avanzado", "Avanzado"


class Partida(models.Model):
    """Una partida del juego. Se crea cuando el usuario entra a la bandeja.

    En «rutas» se guarda la ruta que el usuario tiene abierta en cada ataque:
    {ataque: {"nivel", "etapa", "vistas", "actual", "ultima"}}.
    """

    clave = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    rutas = models.JSONField(default=dict, blank=True)
    iniciada = models.DateTimeField(auto_now_add=True)
    actualizada = models.DateTimeField(auto_now=True)
    completada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-iniciada"]
        verbose_name = "partida"
        verbose_name_plural = "partidas"

    def __str__(self):
        return f"Partida {self.id} ({self.insignias.count()} insignias)"


class Respuesta(models.Model):
    """Cada respuesta que da el usuario a una pregunta."""

    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name="respuestas")
    ataque = models.CharField(max_length=40, db_index=True)
    nivel = models.CharField(max_length=20, choices=Nivel.choices)
    codigo_pregunta = models.CharField(max_length=20)
    texto_elegido = models.CharField(max_length=300)
    es_correcta = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha"]
        indexes = [models.Index(fields=["partida", "ataque", "nivel"])]
        verbose_name = "respuesta"
        verbose_name_plural = "respuestas"

    def __str__(self):
        return f"{self.codigo_pregunta} - {'correcta' if self.es_correcta else 'incorrecta'}"


class InsigniaGanada(models.Model):
    """Insignia que se gana al acertar la pregunta del nivel avanzado de un ataque."""

    partida = models.ForeignKey(Partida, on_delete=models.CASCADE, related_name="insignias")
    ataque = models.CharField(max_length=40)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha"]
        constraints = [models.UniqueConstraint(fields=["partida", "ataque"], name="una_insignia_por_ataque")]
        verbose_name = "insignia ganada"
        verbose_name_plural = "insignias ganadas"

    def __str__(self):
        return f"{self.ataque} ({self.fecha:%d/%m/%Y %H:%M})"
