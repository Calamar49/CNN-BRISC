"""Inferencia de la aplicacion: carga los modelos ONNX desplegados, preprocesa la imagen igual que en el
entrenamiento y aplica las reglas de decision del plan (docs/PLAN_SPRINT3.md seccion 6.3).

Reglas:
  - Si el clasificador predice «sin tumor», NO se muestra mascara (la U-Net nunca vio imagenes sin tumor).
  - Si la probabilidad mas alta es < 0.80 (UMBRAL propuesto, no medido), se marca «confianza baja: requiere
    revision del medico».
  - Se reporta el area del tumor como % de la imagen y las 4 probabilidades.
  - Se valida la entrada: formato PNG/JPG, y el brillo medio del cerebro dentro del rango visto en entrenamiento
    (~36 a ~161 sobre 255); si no, se advierte (el modelo solo conoce T1 con contraste de ese dataset).
"""
import base64
import io
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

import sys
RAIZ_S3 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_S3))
from preprocesado import CLASES, CLASES_ES, preprocesar, sigmoide, softmax  # noqa: E402

REGISTRO = RAIZ_S3 / "modelos"
UMBRAL_CONFIANZA = 0.80          # propuesta, no medido
BRILLO_MIN, BRILLO_MAX = 36, 161  # rango del brillo medio del cerebro en entrenamiento (Sprint 1)
FONDO = 10                        # pixel de fondo si <= 10 sobre 255
MASCARA_RGBA = (255, 93, 93)      # coral de marcado radiologico
VERSION_MODELOS = "v1 (semilla 2024, Sprint 2)"

_sesiones = {}


def _sesion(nombre):
    if nombre not in _sesiones:
        _sesiones[nombre] = ort.InferenceSession(str(REGISTRO / f"{nombre}.onnx"), providers=["CPUExecutionProvider"])
    return _sesiones[nombre]


def _png_base64(arr, modo):
    buf = io.BytesIO()
    Image.fromarray(arr, modo).save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def validar_entrada(im):
    """Devuelve (ok, advertencias). No bloquea: avisa si la imagen no parece una T1 con contraste del dominio."""
    advertencias = []
    g = np.asarray(im.convert("L"), dtype=np.float32)
    cerebro = g[g > FONDO]
    brillo = float(cerebro.mean()) if cerebro.size else 0.0
    if not (BRILLO_MIN <= brillo <= BRILLO_MAX):
        advertencias.append(f"El brillo medio del cerebro ({brillo:.0f}) esta fuera del rango visto en "
                            f"entrenamiento ({BRILLO_MIN}-{BRILLO_MAX}); el modelo solo conoce T1 con contraste.")
    w, h = im.size
    if min(w, h) < 64:
        advertencias.append("La imagen es muy pequena; el resultado puede no ser fiable.")
    return brillo, advertencias


def predecir(im):
    """im: PIL.Image. Devuelve un dict con todo lo que la interfaz necesita."""
    t0 = time.time()
    brillo, advertencias = validar_entrada(im)
    x, gris = preprocesar(im)

    logits_clf = _sesion("clasificador_v1").run(None, {"imagen": x})[0][0]
    probs = softmax(logits_clf)
    idx = int(probs.argmax())
    clase = CLASES[idx]
    confianza = float(probs[idx])
    es_sin_tumor = clase == "no_tumor"
    confianza_baja = confianza < UMBRAL_CONFIANZA

    # segmentacion: solo se usa si NO es «sin tumor»
    mascara_b64, area_pct, hay_region = None, 0.0, False
    if not es_sin_tumor:
        logits_seg = _sesion("segmentacion_v1").run(None, {"imagen": x})[0][0, 0]
        mascara = sigmoide(logits_seg) > 0.5
        area_pct = float(mascara.mean() * 100)
        hay_region = bool(mascara.any())
        rgba = np.zeros((256, 256, 4), np.uint8)
        rgba[mascara, 0], rgba[mascara, 1], rgba[mascara, 2] = MASCARA_RGBA
        rgba[mascara, 3] = 160
        mascara_b64 = _png_base64(rgba, "RGBA")

    return {
        "imagen": _png_base64(gris, "L"),
        "mascara": mascara_b64,
        "clase": clase,
        "clase_es": CLASES_ES[clase],
        "es_sin_tumor": es_sin_tumor,
        "confianza": confianza,
        "confianza_baja": confianza_baja,
        "probabilidades": {CLASES[i]: float(probs[i]) for i in range(len(CLASES))},
        "probabilidades_es": {CLASES_ES[CLASES[i]]: float(probs[i]) for i in range(len(CLASES))},
        "area_pct": round(area_pct, 2),
        "hay_region": hay_region,
        "brillo_medio": round(brillo, 1),
        "advertencias": advertencias,
        "version_modelos": VERSION_MODELOS,
        "tiempo_ms": round((time.time() - t0) * 1000, 1),
    }
