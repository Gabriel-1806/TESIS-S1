# PhishTrain

Prototipo del proyecto de tesis *Ambiente interactivo para el entrenamiento en la identificación de ataques phishing* (Seminario de Investigación I, Universidad de Lima, 2026-2).

Es un juego web que simula una bandeja de Outlook. Cada mensaje de la bandeja es un tipo de ataque (8 en total). Al abrirlo, el usuario recorre una ruta de tres niveles (básico, intermedio y avanzado). En el nivel básico se explica el ataque con sus marcadores y después se hacen preguntas de verificación. Si acierta pasa al siguiente nivel; si se equivoca recibe la explicación y otra pregunta del mismo nivel. Al acertar la pregunta avanzada gana la insignia del ataque.

## Cómo ejecutarlo (Windows)

Requisitos: Python 3.12.

1. Doble clic en `INSTALAR_PHISHTRAIN.bat` (solo la primera vez). Crea el entorno virtual, instala Django, prepara la base de datos y corre las pruebas.
2. Doble clic en `ABRIR_PHISHTRAIN.bat`. Se abre http://127.0.0.1:8001/ en el navegador.

O desde la terminal:

```
git clone https://github.com/Gabriel-1806/TESIS-S1.git
cd TESIS-S1
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001
```

## Organización del código (tres capas, MVC)

```
configuracion/        ajustes de Django y URLs principales
juego/                aplicación del juego
  models.py           Partida, Respuesta e InsigniaGanada
  vistas.py           páginas y API (capa de presentación, lado del servidor)
  logica/             capa lógica: servicio.py y los módulos de gestión
    gestion_mensajes.py, gestion_preguntas.py,
    gestion_entrenamiento.py, gestion_progreso.py
  datos/              capa de datos: lectura del JSON y registro de partidas
  contenido/          phishtrain_contenido.json y su schema
  pruebas/            pruebas automáticas
  management/commands validar_contenido y evaluar_prototipo
plantillas/           portada.html y juego.html
estaticos/
  js/                 navegacion.js, visor.js, entrenamiento.js, api.js, util.js, app.js
  css/juego.css
  img/insignias/      figuras de las insignias
```

La capa lógica no usa nada de Django; recibe y devuelve datos de Python. Por eso se puede probar con un registro en memoria (`juego/datos/registro_memoria.py`) y se podría usar desde otra interfaz.

## Contenido

Todo el contenido (ataques, mensajes, marcadores, preguntas, respuestas e insignias) está en `juego/contenido/phishtrain_contenido.json`. Para agregar un tipo de ataque basta con añadirlo al JSON. Antes de usar un archivo editado conviene revisarlo:

```
python manage.py validar_contenido
```

## Pruebas y validación técnica

```
python manage.py test
python manage.py evaluar_prototipo --salida resultados/evaluacion_prototipo.json
```

`evaluar_prototipo` revisa que el validador detecte errores puestos a propósito en el JSON, simula 1000 jugadores por escenario para revisar las reglas de avance y mide el tiempo de respuesta de la API.

Las respuestas de los usuarios se ven en `/admin/` (crear un usuario con `python manage.py createsuperuser`) y se pueden descargar en CSV.
