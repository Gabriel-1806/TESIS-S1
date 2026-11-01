// Visor del correo: muestra remitente, destinatario, asunto, cuerpo, enlace y adjunto,
// y resalta los marcadores.

import {$, aviso, esc, mostrar} from "./util.js";

export function crearVisor() {
    function barraEstado(visible) {
        const url = $("enlaceCorreo").dataset.url;
        const barra = $("barraEstado");
        barra.textContent = visible && url ? url : "";
        barra.classList.toggle("visible", Boolean(visible && url));
    }

    // Quita el foco del marcador actual. Con todo=true quita también todas las marcas.
    function limpiar(todo) {
        const clases = todo ? ["resaltado", "resaltado-foco", "resaltado-ok"] : ["resaltado-foco"];
        ["correoRemitente", "enlaceCorreo", "adjuntoCorreo"].forEach(id => $(id).classList.remove(...clases));
        $("cuerpoCorreo").querySelectorAll("mark").forEach(m => m.classList.remove("resaltado-foco"));
    }

    function mostrarCorreo(correo, etiqueta) {
        $("asuntoCorreo").textContent = correo.asunto;
        $("avatarCorreo").textContent = (correo.remitente || "?").slice(0, 1).toUpperCase();
        $("nombreRemitente").textContent = correo.remitente;
        $("correoRemitente").textContent = `<${correo.correo_remitente}>`;
        $("destinatarioCorreo").textContent = correo.destinatario;
        $("fechaCorreo").textContent = correo.fecha;
        $("cuerpoCorreo").innerHTML = esc(correo.cuerpo).replaceAll("\n", "<br>");
        const enlace = $("enlaceCorreo");
        enlace.dataset.url = correo.enlace || "";
        enlace.textContent = correo.texto_enlace ? `🔗 ${correo.texto_enlace}` : "";
        mostrar(enlace, Boolean(correo.enlace));
        $("nombreAdjunto").textContent = correo.adjunto || "";
        mostrar($("adjuntoCorreo"), Boolean(correo.adjunto));
        $("etiquetaCorreo").textContent = etiqueta || "";
        mostrar($("etiquetaCorreo"), Boolean(etiqueta));
        barraEstado(false);
        limpiar(true);
    }

    // Pone <mark> en las frases del cuerpo (cada una con su número).
    function marcarFrases(cuerpo, frases, clase) {
        let html = esc(cuerpo);
        frases.forEach(({frase, numero}) => {
            const segura = esc(frase);
            if (frase && html.includes(segura)) html = html.replace(segura, `<mark class="${clase}" data-i="${numero}">${segura}</mark>`);
        });
        $("cuerpoCorreo").innerHTML = html.replaceAll("\n", "<br>");
    }

    function nodoDelLugar(lugar) {
        return {remitente: $("correoRemitente"), enlace: $("enlaceCorreo"), adjunto: $("adjuntoCorreo")}[lugar] || null;
    }

    // Nivel básico: se marcan todos los marcadores del mensaje de la bandeja.
    function marcarTodos(cuerpo, marcadores) {
        marcarFrases(cuerpo, marcadores.map((m, numero) => ({frase: m.lugar === "frase" ? m.frase : "", numero})), "marcador");
        marcadores.forEach(m => { const nodo = nodoDelLugar(m.lugar); if (nodo) nodo.classList.add("resaltado"); });
    }

    // Enfoca el marcador i y devuelve su nodo para poder bajar hasta él.
    function enfocar(marcador, i) {
        limpiar();
        const nodo = marcador.lugar === "frase" ? $("cuerpoCorreo").querySelector(`mark[data-i="${i}"]`) : nodoDelLugar(marcador.lugar);
        if (nodo) nodo.classList.add("resaltado-foco");
        if (marcador.lugar === "enlace") barraEstado(true);
        return nodo;
    }

    // Al mostrar la respuesta, marca en verde el indicio clave de la pregunta.
    function marcarIndicio(indicio, cuerpo) {
        if (!indicio) return;
        const nodo = nodoDelLugar(indicio);
        if (nodo) { nodo.classList.add("resaltado-ok"); if (indicio === "enlace") barraEstado(true); return; }
        marcarFrases(cuerpo, [{frase: indicio, numero: 0}], "marcador resaltado-ok");
    }

    const enlace = $("enlaceCorreo");
    enlace.addEventListener("mouseenter", () => barraEstado(true));
    enlace.addEventListener("focus", () => barraEstado(true));
    enlace.addEventListener("mouseleave", () => barraEstado(false));
    enlace.addEventListener("blur", () => barraEstado(false));
    enlace.addEventListener("click", () => aviso(`Enlace simulado: no se abrió ningún sitio. Su destino real es ${enlace.dataset.url}.`));
    $("adjuntoCorreo").addEventListener("click", () => aviso("Adjunto simulado: no se descargó ningún archivo. Revisa siempre su extensión antes de abrirlo."));

    return {mostrar: mostrarCorreo, marcarTodos, enfocar, marcarIndicio, limpiar};
}
