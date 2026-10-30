"use strict";

// Opacidad y visibilidad del contorno del tumor en el visor del resultado
(function () {
  const overlay = document.getElementById("overlay");
  const ver = document.getElementById("verMascara");
  const op = document.getElementById("opacidad");
  if (!overlay || !ver || !op) return;
  function aplicar() { overlay.style.opacity = ver.checked ? op.value / 100 : 0; }
  ver.addEventListener("change", aplicar);
  op.addEventListener("input", aplicar);
  aplicar();
})();

// Formulario de revisión: habilitar el selector de clase solo al corregir
function togglePlan(corregir) {
  const sel = document.getElementById("selClase");
  if (sel) sel.disabled = !corregir;
}
window.togglePlan = togglePlan;

// Mostrar el nombre del archivo elegido y el indicador de "procesando" al enviar
(function () {
  const entrada = document.getElementById("entradaArchivo");
  if (entrada) {
    entrada.addEventListener("change", function () {
      const txt = document.querySelector(".archivo-texto");
      if (txt && entrada.files[0]) txt.textContent = entrada.files[0].name;
    });
  }
  const form = document.getElementById("formEstudio");
  if (form) {
    form.addEventListener("submit", function () {
      const p = document.getElementById("procesando");
      if (p) p.hidden = false;
    });
  }
})();
