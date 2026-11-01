class ErrorJuego(Exception):
    """Error de una acción del juego. Lleva el código HTTP que se devuelve en la API."""

    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
