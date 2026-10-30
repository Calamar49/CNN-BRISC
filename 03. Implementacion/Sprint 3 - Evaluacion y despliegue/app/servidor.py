"""Backend de la aplicacion web de demostracion (HU13). Sirve los modelos ONNX finales con onnxruntime.

NO es una herramienta de diagnostico: es una demostracion academica. Recibe una imagen de resonancia,
predice el tipo de tumor (clasificacion) y marca su contorno (segmentacion), y devuelve todo en JSON para que
la interfaz lo muestre en el visor.

Uso:
    cd "03. Implementacion/Sprint 3 - Evaluacion y despliegue"
    ../../.venv/Scripts/python.exe -m uvicorn app.servidor:app --port 8000
Luego abrir http://localhost:8000
"""
import base64
import io
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

AQUI = Path(__file__).resolve().parent
RAIZ_S3 = AQUI.parent
sys.path.insert(0, str(RAIZ_S3))
from preprocesado import CLASES, CLASES_ES, preprocesar, sigmoide, softmax  # noqa: E402

REGISTRO = RAIZ_S3 / "modelos"
ESTATICO = AQUI / "estatico"
EJEMPLOS = ESTATICO / "ejemplos"
MASCARA_RGBA = (255, 93, 93)  # coral de marcado radiologico para el overlay del tumor

app = FastAPI(title="BRISC — demostracion academica", docs_url="/api/docs")
_sesiones = {}


def sesion(nombre):
    if nombre not in _sesiones:
        provs = ort.get_available_providers()
        prov = ["CPUExecutionProvider"]  # CPU: mas portable para un demo; el modelo es chico
        _sesiones[nombre] = ort.InferenceSession(str(REGISTRO / f"{nombre}.onnx"), providers=prov)
    return _sesiones[nombre]


def _png_base64(arr_uint8, modo="L"):
    im = Image.fromarray(arr_uint8, modo)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _preparar_ejemplos():
    """Copia unas imagenes reales de la prueba oficial al estatico, para probar sin subir nada.
    La carpeta ejemplos/ esta ignorada por Git (son imagenes del dataset)."""
    if EJEMPLOS.exists() and list(EJEMPLOS.glob("*.png")):
        return
    import os
    import pandas as pd
    raiz = Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))
    man_path = raiz / "manifest_preparado.csv"
    if not man_path.exists():
        return
    EJEMPLOS.mkdir(parents=True, exist_ok=True)
    man = pd.read_csv(man_path)
    test = man[man.particion == "test"]
    for clase in CLASES:
        sub = test[test.clase == clase].head(2)
        for i, r in enumerate(sub.itertuples()):
            try:
                Image.open(raiz / r.ruta_imagen).save(EJEMPLOS / f"{clase}_{i+1}.png")
            except Exception:
                pass


def _predecir(im):
    x, gris = preprocesar(im)
    logits_clf = sesion("clasificador_final").run(None, {"entrada": x})[0][0]
    probs = softmax(logits_clf)
    idx = int(probs.argmax())
    logits_seg = sesion("unet_final").run(None, {"entrada": x})[0][0, 0]
    mascara = (sigmoide(logits_seg) > 0.5)
    area_pct = float(mascara.mean() * 100)

    rgba = np.zeros((256, 256, 4), dtype=np.uint8)
    rgba[mascara, 0], rgba[mascara, 1], rgba[mascara, 2] = MASCARA_RGBA
    rgba[mascara, 3] = 150

    return {
        "imagen": _png_base64(gris, "L"),
        "mascara": _png_base64(rgba, "RGBA"),
        "clasificacion": {
            "clase": CLASES[idx],
            "clase_es": CLASES_ES[CLASES[idx]],
            "confianza": float(probs[idx]),
            "probabilidades": {CLASES[i]: float(probs[i]) for i in range(len(CLASES))},
            "es_sin_tumor": CLASES[idx] == "no_tumor",
        },
        "segmentacion": {
            "area_pct": round(area_pct, 2),
            "hay_region": bool(mascara.any()),
        },
    }


@app.post("/api/predecir")
async def predecir(archivo: UploadFile = File(...)):
    contenido = await archivo.read()
    im = Image.open(io.BytesIO(contenido))
    return _predecir(im)


@app.get("/api/ejemplos")
async def ejemplos():
    _preparar_ejemplos()
    if not EJEMPLOS.exists():
        return {"ejemplos": []}
    archivos = sorted(p.name for p in EJEMPLOS.glob("*.png"))
    return {"ejemplos": [{"nombre": a, "url": f"/ejemplos/{a}", "clase_real": a.rsplit("_", 1)[0]} for a in archivos]}


@app.get("/")
async def inicio():
    return FileResponse(ESTATICO / "index.html")


_preparar_ejemplos()
app.mount("/ejemplos", StaticFiles(directory=str(EJEMPLOS)) if EJEMPLOS.exists() else StaticFiles(directory=str(ESTATICO)), name="ejemplos")
app.mount("/", StaticFiles(directory=str(ESTATICO)), name="estatico")
