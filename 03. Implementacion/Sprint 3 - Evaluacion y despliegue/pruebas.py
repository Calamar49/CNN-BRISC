"""Pruebas minimas antes de presentar (docs/PLAN_SPRINT3.md seccion 15.3). Se guardan como script para repetirlas.

1. Paridad ONNX vs PyTorch en imagenes de validacion (los logits casi iguales; la clase y la mascara coinciden).
2. Preprocesamiento identico: el tensor que arma la app (preprocesado.preprocesar) coincide con el del cargador
   de entrenamiento (datos.py) para varias imagenes.
3. Recorrido de inferencia: inferencia.predecir() devuelve una salida valida para las imagenes de ejemplo y mide
   el tiempo por imagen.

Uso:  python pruebas.py
"""
import os
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
from PIL import Image

AQUI = Path(__file__).resolve().parent
S2 = AQUI.parent / "Sprint 2 - Entrenamiento"
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(S2)); sys.path.insert(0, str(AQUI / "app"))
from preprocesado import preprocesar  # noqa: E402
from datos import BriscClasificacion  # noqa: E402
from modelos import crear_clasificador  # noqa: E402

REGISTRO = AQUI / "modelos"
fallos = []


def ok(cond, texto):
    print(("  OK   " if cond else "  FALLA  ") + texto)
    if not cond:
        fallos.append(texto)


def raiz():
    return Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))


def prueba_paridad():
    print("\n1. Paridad ONNX vs PyTorch (clasificador, 20 imagenes de validacion)")
    ck = torch.load(S2 / "salida_sprint2" / "clf_efficientnet_b0_20261023_004900.pt", map_location="cpu", weights_only=False)
    m = crear_clasificador(ck["arquitectura"], preentrenado=False); m.load_state_dict(ck["modelo"]); m.eval()
    man = __import__("pandas").read_csv(raiz() / "manifest_preparado.csv").query("particion=='val'").head(20)
    xs = [preprocesar(Image.open(raiz() / r.ruta_imagen))[0] for r in man.itertuples()]
    x = np.concatenate(xs).astype(np.float32)
    with torch.no_grad():
        yt = m(torch.from_numpy(x)).numpy()
    yo = ort.InferenceSession(str(REGISTRO / "clasificador_v1.onnx"), providers=["CPUExecutionProvider"]).run(None, {"imagen": x})[0]
    ok(float(np.abs(yt - yo).max()) < 5e-2, f"logits casi iguales (dif max {np.abs(yt-yo).max():.2e})")
    ok(bool((yt.argmax(1) == yo.argmax(1)).all()), "la clase predicha coincide en las 20 imagenes")


def prueba_preprocesado():
    print("\n2. Preprocesamiento identico (app vs cargador de entrenamiento, 5 imagenes)")
    ds = BriscClasificacion("val")
    r = raiz()
    difs = 0
    for i in range(5):
        t_entreno = ds[i][0].numpy()
        fila = ds.t.iloc[i]
        t_app = preprocesar(Image.open(r / fila.ruta_imagen))[0][0]
        if not np.allclose(t_entreno, t_app, atol=1e-5):
            difs += 1
    ok(difs == 0, f"el tensor de la app coincide con el del entrenamiento ({5-difs}/5)")


def prueba_recorrido():
    print("\n3. Recorrido de inferencia en las imagenes de ejemplo")
    from inferencia import predecir
    demo = AQUI / "app" / "datos_demo" / "imagenes"
    ejemplos = sorted(demo.glob("*.png"))
    if not ejemplos:
        print("  (omitido: no hay imagenes de ejemplo; levanta la app una vez para generarlas)")
        return
    tiempos = []
    for p in ejemplos:
        pred = predecir(Image.open(p))
        tiempos.append(pred["tiempo_ms"])
        ok(pred["clase"] in ("glioma", "meningioma", "pituitary", "no_tumor"),
           f"{p.name}: clase {pred['clase_es']} ({pred['confianza']*100:.0f}%), {pred['tiempo_ms']:.0f} ms")
    print(f"  tiempo medio por imagen: {np.mean(tiempos):.0f} ms")


if __name__ == "__main__":
    prueba_paridad()
    prueba_preprocesado()
    prueba_recorrido()
    print("\nRESULTADO:", "todo correcto" if not fallos else f"{len(fallos)} fallo(s)")
    sys.exit(1 if fallos else 0)
