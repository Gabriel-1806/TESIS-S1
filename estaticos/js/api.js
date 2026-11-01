// Comunicación con el servidor. La presentación solo habla con la capa lógica por aquí.
// Hay una función por cada operación del servicio del juego.

function tokenCsrf() {
    const campo = document.querySelector("input[name=csrfmiddlewaretoken]");
    return campo ? campo.value : "";
}

async function pedir(url, cuerpo) {
    const opciones = {credentials: "same-origin", headers: {"Accept": "application/json"}};
    if (cuerpo !== undefined) {
        opciones.method = "POST";
        opciones.headers["Content-Type"] = "application/json";
        opciones.headers["X-CSRFToken"] = tokenCsrf();
        opciones.body = JSON.stringify(cuerpo);
    }
    const respuesta = await fetch(url, opciones);
    let datos;
    try { datos = await respuesta.json(); } catch (_) { datos = {ok: false, mensaje: "El servidor devolvió una respuesta no válida."}; }
    if (!respuesta.ok || datos.ok === false) throw new Error(datos.mensaje || "No se pudo completar la acción.");
    return datos;
}

export function crearApi(contenedor) {
    const urls = contenedor.dataset;
    return {
        estado: () => pedir(urls.urlEstado),
        abrir: ataque => pedir(urls.urlAbrir, {ataque}),
        pregunta: ataque => pedir(urls.urlPregunta, {ataque}),
        responder: (ataque, elegida) => pedir(urls.urlResponder, {ataque, elegida}),
    };
}
