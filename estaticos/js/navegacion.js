// Navegación: bandeja de entrada, Mi progreso y Mis insignias,
// y el contador de insignias de la barra superior.

import {$, NIVELES, NOMBRE_NIVEL, esc, mostrar} from "./util.js";

export function crearNavegacion({contenedor, api, rutaActual, alAbrir}) {
    let estado = null;
    let vista = "bandeja";

    function cerrarMenu() { $("menu").classList.remove("abierto"); mostrar($("fondoMenu"), false); }

    function mostrarVista(nombre) {
        vista = nombre;
        const ruta = rutaActual();
        const enBandeja = nombre === "bandeja";
        const completado = Boolean(estado && estado.completado);
        document.querySelectorAll(".menu-item").forEach(b => b.classList.toggle("activo", b.dataset.vista === nombre));
        mostrar($("vistaProgreso"), nombre === "progreso");
        mostrar($("vistaInsignias"), nombre === "insignias");
        mostrar($("vistaRuta"), enBandeja && Boolean(ruta));
        mostrar($("vistaVacia"), enBandeja && !ruta && !completado);
        mostrar($("vistaCompletado"), enBandeja && !ruta && completado);
        contenedor.classList.toggle("ruta-abierta", enBandeja && Boolean(ruta));
        cerrarMenu();
    }

    function dibujarBandeja() {
        if (!estado) return;
        const ruta = rutaActual();
        const pendientes = estado.ataques.filter(a => !a.ganada);
        $("textoLista").textContent = pendientes.length
            ? `${pendientes.length} mensaje${pendientes.length > 1 ? "s" : ""}: uno por cada tipo de ataque que te falta.`
            : "¡Bandeja vacía! Ya ganaste todas las insignias.";
        if (!pendientes.length) {
            $("listaCorreos").innerHTML = '<p class="lista-vacia">No quedan mensajes por revisar. 🏆</p>';
            return;
        }
        $("listaCorreos").innerHTML = pendientes.map(a => {
            const llego = a.nivel_alcanzado && a.nivel_alcanzado !== "basico"
                ? `<span class="etiqueta etiqueta-avance">Llegaste a: ${esc(NOMBRE_NIVEL[a.nivel_alcanzado])}</span>` : "";
            const adjunto = a.tiene_adjunto ? '<span class="etiqueta etiqueta-simple">📎 Adjunto</span>' : "";
            return `
            <article class="item-correo ${ruta && ruta.ataque === a.clave ? "seleccionado" : ""} ${a.respondidas ? "" : "no-leido"}" role="listitem" tabindex="0"
                     data-ataque="${esc(a.clave)}" aria-label="${esc(`Ataque ${a.numero}: ${a.nombre}. Mensaje de ${a.remitente}: ${a.asunto}`)}">
                <span class="avatar">${esc(a.remitente.slice(0, 1).toUpperCase())}</span>
                <div class="item-resumen">
                    <div class="item-fila"><strong>${esc(a.remitente)}</strong><time>${esc(a.fecha)}</time></div>
                    <b>${esc(a.asunto)}</b>
                    <p>${esc(a.vista_previa)}</p>
                    <span class="item-etiquetas"><span class="etiqueta">${a.icono} Ataque ${a.numero} · ${esc(a.nombre)}</span>${llego}${adjunto}</span>
                </div>
            </article>`;
        }).join("");
    }

    function celdaNivel(ataque, nivel) {
        const alcanzado = ataque.nivel_alcanzado === "insignia" ? 3 : NIVELES.indexOf(ataque.nivel_alcanzado);
        const i = NIVELES.indexOf(nivel);
        const clase = ataque.ganada || i < alcanzado ? "hecho" : i === alcanzado ? "actual" : "";
        return `<span class="punto-nivel ${clase}" title="${esc(NOMBRE_NIVEL[nivel])}">${clase === "hecho" ? "✓" : ""}</span>`;
    }

    function dibujarProgreso() {
        $("resumenProgreso").innerHTML = `
            <div><strong>${estado.insignias} de ${estado.total}</strong><span>insignias</span></div>
            <div><strong>${estado.respondidas}</strong><span>preguntas respondidas</span></div>
            <div><strong>${estado.correctas}</strong><span>respuestas correctas</span></div>`;
        const cabecera = `<div class="fila fila-cabecera" role="row"><span role="columnheader">Tipo de ataque</span><span role="columnheader">Básico</span><span role="columnheader">Intermedio</span><span role="columnheader">Avanzado</span><span role="columnheader">Estado</span></div>`;
        $("tablaProgreso").innerHTML = cabecera + estado.ataques.map(a => {
            const situacion = a.ganada ? '<span class="etiqueta etiqueta-ok">★ Insignia</span>'
                : a.nivel_alcanzado ? `<span class="etiqueta etiqueta-avance">Llegó a ${esc(NOMBRE_NIVEL[a.nivel_alcanzado])}</span>`
                : '<span class="etiqueta etiqueta-simple">Sin empezar</span>';
            return `<div class="fila" role="row"><span role="cell">${a.icono} ${esc(a.nombre)}</span>${NIVELES.map(n => `<span role="cell">${celdaNivel(a, n)}</span>`).join("")}<span role="cell">${situacion}</span></div>`;
        }).join("");
        $("listaNiveles").innerHTML = estado.niveles.map(n => `<li><b>${esc(n.nombre)}:</b> ${esc(n.contenido)}</li>`).join("");
    }

    function tarjetasInsignias(lista, chica) {
        return lista.map(a => `
            <div class="insignia ${a.ganada ? "ganada" : "bloqueada"}">
                <img class="insignia-img" src="${esc(a.imagen_insignia)}" alt="" aria-hidden="true">
                <strong>${esc(a.insignia)}</strong>
                ${chica ? "" : `<small>${esc(a.nombre)}</small><span class="insignia-estado">${a.ganada ? "Conquistada" : "Pendiente"}</span>`}
            </div>`).join("");
    }

    function dibujarInsignias() {
        $("grillaInsignias").innerHTML = tarjetasInsignias(estado.ataques, false);
        $("insigniasCompletado").innerHTML = tarjetasInsignias(estado.ataques, true);
    }

    // Pinta el estado que devuelve el servidor (gestión del progreso e insignias).
    function aplicarEstado(nuevo) {
        estado = nuevo;
        $("contadorInsignias").textContent = estado.insignias;
        $("totalInsignias").textContent = estado.total;
        $("contadorBandeja").textContent = estado.ataques.filter(a => !a.ganada).length;
        $("contadorMisInsignias").textContent = estado.insignias;
        $("totalCompletado").textContent = estado.total;
        dibujarBandeja();
        dibujarProgreso();
        dibujarInsignias();
        if (!rutaActual()) mostrarVista(vista);
    }

    async function actualizar() {
        try {
            const datos = await api.estado();
            aplicarEstado(datos.estado);
        } catch (error) {
            $("listaCorreos").innerHTML = `<p class="lista-vacia">No se pudieron cargar los mensajes. ${esc(error.message)} <button type="button" class="enlace-texto" id="botonReintentar">Reintentar</button></p>`;
            $("botonReintentar").addEventListener("click", actualizar);
        }
    }

    function alElegirMensaje(evento) {
        const item = evento.target.closest(".item-correo[data-ataque]");
        if (!item) return;
        if (evento.type === "keydown" && evento.key !== "Enter" && evento.key !== " ") return;
        evento.preventDefault();
        const ruta = rutaActual();
        if (ruta && ruta.ataque === item.dataset.ataque) { mostrarVista("bandeja"); return; }
        alAbrir(item.dataset.ataque);
    }
    $("listaCorreos").addEventListener("click", alElegirMensaje);
    $("listaCorreos").addEventListener("keydown", alElegirMensaje);

    document.querySelectorAll(".menu-item").forEach(b => b.addEventListener("click", () => mostrarVista(b.dataset.vista)));
    document.querySelectorAll("[data-ir]").forEach(b => b.addEventListener("click", () => mostrarVista(b.dataset.ir)));
    $("botonMenu").addEventListener("click", () => {
        const abrir = !$("menu").classList.contains("abierto");
        $("menu").classList.toggle("abierto", abrir);
        mostrar($("fondoMenu"), abrir);
    });
    $("fondoMenu").addEventListener("click", cerrarMenu);

    return {
        mostrarVista, dibujarBandeja, aplicarEstado, actualizar,
        total: () => (estado ? estado.total : ""),
    };
}
