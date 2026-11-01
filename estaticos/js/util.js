// Funciones que usan varios módulos de la presentación.

export const $ = id => document.getElementById(id);

export const NIVELES = ["basico", "intermedio", "avanzado"];
export const NOMBRE_NIVEL = {basico: "Básico", intermedio: "Intermedio", avanzado: "Avanzado", insignia: "Insignia"};

// Escapa el texto antes de ponerlo en innerHTML.
export function esc(valor) {
    return String(valor ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

export function mostrar(nodo, visible) {
    if (nodo) nodo.classList.toggle("oculto", !visible);
}

export function aviso(texto) {
    const nodo = $("aviso");
    nodo.textContent = texto;
    nodo.classList.add("visible");
    window.clearTimeout(aviso.temporizador);
    aviso.temporizador = window.setTimeout(() => nodo.classList.remove("visible"), 3800);
}

export function desplazarHasta(nodo) {
    if (nodo) window.setTimeout(() => nodo.scrollIntoView({behavior: "smooth", block: "nearest"}), 40);
}
