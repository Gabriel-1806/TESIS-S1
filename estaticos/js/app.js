// Arranque de la pantalla del juego.
// La presentación tiene tres módulos, como en la arquitectura:
//   navegacion.js     bandeja de entrada, Mi progreso y Mis insignias
//   visor.js          el correo con sus marcadores resaltados
//   entrenamiento.js  el área de entrenamiento guiado
// Ninguno decide las reglas del juego; todos piden los datos con api.js.

import {crearApi} from "./api.js";
import {crearEntrenamiento} from "./entrenamiento.js";
import {crearNavegacion} from "./navegacion.js";
import {crearVisor} from "./visor.js";

const contenedor = document.getElementById("juego");
if (contenedor) {
    const api = crearApi(contenedor);
    const visor = crearVisor();
    let entrenamiento = null;
    const navegacion = crearNavegacion({
        contenedor,
        api,
        rutaActual: () => (entrenamiento ? entrenamiento.ruta() : null),
        alAbrir: clave => entrenamiento.abrir(clave),
    });
    entrenamiento = crearEntrenamiento({api, visor, navegacion});
    navegacion.actualizar();
}
