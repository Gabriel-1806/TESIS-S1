

import {$, NIVELES, aviso, desplazarHasta, esc} from "./util.js";

const LETRAS = ["A", "B", "C", "D", "E"];

export function crearEntrenamiento({api, visor, navegacion}) {
    let ruta = null;   

    function marcarPasos(actual) {
        const indice = actual === "insignia" ? 3 : NIVELES.indexOf(actual);
        document.querySelectorAll("#pasosNivel li").forEach((li, i) => {
            li.className = i < indice ? "hecho" : i === indice ? "actual" : "";
        });
    }

    function pintarArea(modo, paso, html) {
        $("areaEntrenamiento").className = `entrenamiento entrenamiento-${modo}`;
        $("pasoEntrenamiento").textContent = paso;
        $("cuerpoEntrenamiento").innerHTML = html;
    }

    async function abrir(clave) {
        if (ruta && ruta.ocupado) return;
        try {
            const datos = await api.abrir(clave);
            ruta = {ataque: clave, info: datos.ataque, correo: datos.correo, etapa: "inicio", marcador: -1, nivel: "basico", ocupado: false};
            $("rutaNumero").textContent = `ATAQUE ${datos.ataque.numero} DE ${navegacion.total()}`;
            $("rutaNombre").textContent = `${datos.ataque.icono} ${datos.ataque.nombre}`;
            marcarPasos("basico");
            navegacion.mostrarVista("bandeja");
            navegacion.dibujarBandeja();
            visor.mostrar(datos.correo, "");
            visor.marcarTodos(datos.correo.cuerpo, datos.ataque.marcadores);
            caracterizacion();
            $("lector").scrollTop = 0;
        } catch (error) {
            aviso(error.message);
            navegacion.actualizar();
        }
    }

    function salir() {
        ruta = null;
        visor.limpiar(true);
        navegacion.mostrarVista("bandeja");
        navegacion.dibujarBandeja();
        navegacion.actualizar();
    }

    
    function caracterizacion() {
        const info = ruta.info;
        const i = ruta.marcador;
        const total = info.marcadores.length;
        if (i < 0) {
            visor.limpiar();
            pintarArea("explicacion", "NIVEL BÁSICO · CONOCE EL ATAQUE", `
                <h3>¿Qué es ${esc(info.nombre)}?</h3>
                <p>${esc(info.definicion)}</p>
                <p class="nota">En el mensaje de arriba están marcados sus indicios. Te los explico uno por uno.</p>
                <div class="entrenamiento-acciones"><button type="button" class="boton boton-principal" data-accion="siguiente">Ver los indicios (${total}) →</button></div>`);
            return;
        }
        if (i >= total) {
            visor.limpiar();
            pintarArea("explicacion", "NIVEL BÁSICO · CONOCE EL ATAQUE", `
                <h3>Resumen: así se reconoce</h3>
                <ul class="lista-check">${info.marcadores.map(m => `<li>${esc(m.titulo)}</li>`).join("")}</ul>
                <p><b>Qué hacer:</b> ${esc(info.que_hacer)}</p>
                <p class="nota">Ahora vamos a verificar lo que comprendiste.</p>
                <div class="entrenamiento-acciones">
                    <button type="button" class="boton boton-secundario" data-accion="anterior">← Anterior</button>
                    <button type="button" class="boton boton-principal" data-accion="preguntar">Verificar lo que aprendí →</button>
                </div>`);
            return;
        }
        const marcador = info.marcadores[i];
        desplazarHasta(visor.enfocar(marcador, i));
        pintarArea("explicacion", `NIVEL BÁSICO · INDICIO ${i + 1} DE ${total}`, `
            <div class="puntos" aria-hidden="true">${info.marcadores.map((_, k) => `<i class="${k <= i ? "encendido" : ""}"></i>`).join("")}</div>
            <h3>${esc(marcador.titulo)}</h3>
            <p>${esc(marcador.texto)}</p>
            <div class="entrenamiento-acciones">
                <button type="button" class="boton boton-secundario" data-accion="anterior">← Anterior</button>
                <button type="button" class="boton boton-principal" data-accion="siguiente">${i === total - 1 ? "Ver resumen →" : "Siguiente indicio →"}</button>
            </div>`);
    }

    async function preguntar() {
        if (!ruta || ruta.ocupado) return;
        ruta.ocupado = true;
        try {
            const pregunta = (await api.pregunta(ruta.ataque)).pregunta;
            ruta.etapa = "pregunta";
            ruta.nivel = pregunta.nivel.clave;
            ruta.pregunta = pregunta;
            $("areaEntrenamiento").dataset.codigo = pregunta.codigo;
            marcarPasos(ruta.nivel);
            visor.mostrar(pregunta.correo, `Mensaje de ejemplo · Nivel ${pregunta.nivel.nombre}`);
            pintarArea("pregunta", `NIVEL ${pregunta.nivel.nombre.toUpperCase()} · PREGUNTA`, `
                <p class="nota">Lee el mensaje de arriba y responde.</p>
                <h3>${esc(pregunta.enunciado)}</h3>
                <div class="opciones" role="group" aria-label="Respuestas posibles">
                    ${pregunta.opciones.map((texto, k) => `<button type="button" class="opcion" data-opcion="${k}"><span class="letra">${LETRAS[k]}</span><span>${esc(texto)}</span></button>`).join("")}
                </div>`);
            $("lector").scrollTop = 0;
        } catch (error) {
            aviso(error.message);
        } finally {
            ruta.ocupado = false;
        }
    }

    async function responder(indice) {
        if (!ruta || ruta.ocupado || ruta.etapa !== "pregunta") return;
        ruta.ocupado = true;
        const botones = Array.from(document.querySelectorAll(".opcion"));
        botones.forEach(b => { b.disabled = true; });
        try {
            const datos = await api.responder(ruta.ataque, indice);
            ruta.etapa = datos.insignia ? "insignia" : "retroalimentacion";
            botones[datos.posicion_correcta].classList.add("correcta");
            if (!datos.correcta) botones[indice].classList.add("incorrecta");
            visor.marcarIndicio(datos.indicio, ruta.pregunta.correo.cuerpo);
            retroalimentacion(datos);
            navegacion.aplicarEstado(datos.estado);
        } catch (error) {
            aviso(error.message);
            botones.forEach(b => { b.disabled = false; });
        } finally {
            if (ruta) ruta.ocupado = false;
        }
    }

    function retroalimentacion(datos) {
        const opciones = $("cuerpoEntrenamiento").querySelector(".opciones").outerHTML;
        const nivel = datos.nivel.nombre;
        let resultado;
        let boton;
        if (datos.insignia) {
            marcarPasos("insignia");
            resultado = `
                <div class="resultado bien"><strong>¡Felicitaciones! Respuesta correcta.</strong><p>${esc(datos.retro_elegida)}</p></div>
                <div class="insignia-ganada">
                    <img class="insignia-ganada-img" src="${esc(datos.insignia.imagen)}" alt="" aria-hidden="true">
                    <div><small>¡INSIGNIA CONQUISTADA!</small><strong>${esc(datos.insignia.nombre)}</strong>
                    <p>Completaste la ruta de ${esc(datos.insignia.nombre_ataque)}: básico, intermedio y avanzado. Este mensaje ya no aparecerá en tu bandeja.</p></div>
                </div>`;
            boton = `<button type="button" class="boton boton-principal" data-accion="salir">Volver a la bandeja →</button>`;
        } else if (datos.correcta) {
            resultado = `<div class="resultado bien"><strong>¡Felicitaciones! Respuesta correcta.</strong><p>${esc(datos.retro_elegida)}</p></div>`;
            boton = `<button type="button" class="boton boton-principal" data-accion="preguntar">Siguiente nivel: ${esc(datos.siguiente_nivel.nombre)} →</button>`;
        } else {
            resultado = `
                <div class="resultado mal"><strong>Esa no es la respuesta correcta.</strong><p>${esc(datos.retro_elegida)}</p>
                <p class="respuesta-correcta"><b>La respuesta correcta es:</b> ${esc(datos.texto_correcto)}</p><p>${esc(datos.retro_correcta)}</p></div>`;
            boton = `<button type="button" class="boton boton-principal" data-accion="preguntar">Otra pregunta del nivel ${esc(nivel)} →</button>`;
        }
        const modo = datos.insignia ? "insignia" : datos.correcta ? "bien" : "mal";
        pintarArea(modo, `NIVEL ${nivel.toUpperCase()} · ${datos.correcta ? "RESPUESTA CORRECTA" : "RESPUESTA INCORRECTA"}`,
            `<h3>${esc(ruta.pregunta.enunciado)}</h3>${opciones}${resultado}<div class="entrenamiento-acciones">${boton}</div>`);
        desplazarHasta($("areaEntrenamiento").querySelector(".entrenamiento-acciones"));
    }

    $("cuerpoEntrenamiento").addEventListener("click", evento => {
        const opcion = evento.target.closest(".opcion[data-opcion]");
        if (opcion && !opcion.disabled) { responder(Number(opcion.dataset.opcion)); return; }
        const boton = evento.target.closest("[data-accion]");
        if (!boton || !ruta) return;
        const accion = boton.dataset.accion;
        if (accion === "siguiente") { ruta.marcador += 1; caracterizacion(); }
        else if (accion === "anterior") { ruta.marcador = Math.max(-1, ruta.marcador - 1); caracterizacion(); }
        else if (accion === "preguntar") preguntar();
        else if (accion === "salir") salir();
    });
    $("botonVolver").addEventListener("click", salir);

    return {abrir, ruta: () => ruta};
}
