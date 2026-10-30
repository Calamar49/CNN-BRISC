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
  for (const id of ["formEstudio", "formPaciente"]) {
    const form = document.getElementById(id);
    if (form) {
      form.addEventListener("submit", function () {
        const p = document.getElementById("procesando");
        if (p) p.hidden = false;
        const b = document.getElementById("botonAnalizar");
        if (b) { b.disabled = true; b.textContent = "Procesando…"; }
      });
    }
  }
})();

// Formulario de nuevo paciente: mostrar el campo de texto si el motivo es "Otro"
function verOtro() {
  const sel = document.getElementById("selMotivo");
  const campo = document.getElementById("campoOtro");
  if (sel && campo) campo.hidden = sel.value !== "__otro__";
}
window.verOtro = verOtro;
