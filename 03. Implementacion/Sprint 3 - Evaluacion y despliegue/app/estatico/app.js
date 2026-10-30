"use strict";

const CLASES_ES = {
  glioma: "Glioma", meningioma: "Meningioma",
  pituitary: "Tumor de hipófisis", no_tumor: "Sin tumor",
};

const $ = (id) => document.getElementById(id);
const lienzo = $("lienzo"), vacio = $("vacio"), imagenCaja = $("imagenCaja");
const imagenBase = $("imagenBase"), imagenMascara = $("imagenMascara");
const controles = $("controles"), verMascara = $("verMascara"), opacidad = $("opacidad");
const espera = $("espera"), lectura = $("lectura");

function aplicarOpacidad() {
  imagenMascara.style.opacity = verMascara.checked ? (opacidad.value / 100) : 0;
}
verMascara.addEventListener("change", aplicarOpacidad);
opacidad.addEventListener("input", aplicarOpacidad);

async function enviar(archivo) {
  lienzo.classList.add("cargando");
  espera.hidden = false;
  espera.innerHTML = '<p class="insignia-cargando">Analizando la resonancia…</p>';
  lectura.hidden = true;
  try {
    const fd = new FormData();
    fd.append("archivo", archivo);
    const resp = await fetch("/api/predecir", { method: "POST", body: fd });
    if (!resp.ok) throw new Error("respuesta " + resp.status);
    const datos = await resp.json();
    mostrar(datos);
  } catch (e) {
    espera.hidden = false;
    espera.innerHTML = '<p class="insignia-cargando">No se pudo analizar la imagen. Revisa que sea un PNG o JPG.</p>';
  } finally {
    lienzo.classList.remove("cargando");
  }
}

function mostrar(d) {
  imagenBase.src = d.imagen;
  imagenMascara.src = d.mascara;
  vacio.hidden = true;
  imagenCaja.hidden = false;
  controles.hidden = false;
  aplicarOpacidad();

  const c = d.clasificacion;
  const ganadora = $("claseGanadora");
  ganadora.textContent = c.clase_es;
  ganadora.classList.toggle("sin-tumor", c.es_sin_tumor);
  $("confianza").textContent = "confianza " + (c.confianza * 100).toFixed(1) + "%";

  const probs = $("probs");
  probs.innerHTML = "";
  const orden = Object.entries(c.probabilidades).sort((a, b) => b[1] - a[1]);
  for (const [clase, p] of orden) {
    const li = document.createElement("li");
    if (clase === c.clase) li.classList.add("lider");
    li.innerHTML =
      '<span class="nom">' + CLASES_ES[clase] + '</span>' +
      '<span class="barra"><span class="relleno" style="width:' + (p * 100).toFixed(1) + '%"></span></span>' +
      '<span class="val">' + (p * 100).toFixed(1) + '%</span>';
    probs.appendChild(li);
  }

  const s = d.segmentacion;
  const area = $("area"), region = $("region");
  area.textContent = s.area_pct.toFixed(2) + "%";
  area.classList.toggle("coral", s.hay_region);
  region.textContent = s.hay_region ? "sí" : "no";
  $("notaSeg").textContent = c.es_sin_tumor
    ? "El clasificador indicó «sin tumor»: en ese caso la segmentación es solo informativa."
    : "El contorno coral marca la región que el modelo identifica como tumor.";

  espera.hidden = true;
  lectura.hidden = false;
}

// carga de archivo
for (const id of ["archivo", "archivo2"]) {
  $(id).addEventListener("change", (e) => {
    if (e.target.files[0]) enviar(e.target.files[0]);
  });
}

// arrastrar y soltar
["dragover", "dragenter"].forEach((ev) =>
  lienzo.addEventListener(ev, (e) => { e.preventDefault(); lienzo.style.outline = "1px dashed var(--senal)"; }));
["dragleave", "drop"].forEach((ev) =>
  lienzo.addEventListener(ev, (e) => { e.preventDefault(); lienzo.style.outline = "none"; }));
lienzo.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files[0];
  if (f) enviar(f);
});

// ejemplos reales
async function cargarEjemplos() {
  try {
    const resp = await fetch("/api/ejemplos");
    const { ejemplos } = await resp.json();
    const tira = $("tira");
    for (const ej of ejemplos) {
      const b = document.createElement("button");
      b.className = "miniatura";
      b.innerHTML = '<img src="' + ej.url + '" alt=""><span class="etq">' +
        (CLASES_ES[ej.clase_real] || ej.clase_real) + '</span>';
      b.addEventListener("click", async () => {
        const blob = await (await fetch(ej.url)).blob();
        enviar(new File([blob], ej.nombre, { type: "image/png" }));
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      tira.appendChild(b);
    }
  } catch (e) { /* sin ejemplos disponibles */ }
}
cargarEjemplos();
