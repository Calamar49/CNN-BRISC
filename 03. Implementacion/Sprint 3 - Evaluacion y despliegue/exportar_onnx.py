"""Exporta a ONNX los modelos que se DESPLIEGAN (los mejores por validacion del Sprint 2: semilla 2024 en ambas
tareas, segun docs/PLAN_SPRINT3.md seccion 5) y verifica la paridad PyTorch<->ONNX en imagenes reales de
validacion. Genera la tarjeta de modelo con SHA-256 y versiones (para el registro de modelos, HU14).

ONNX permite servir el modelo sin PyTorch (la app usa onnxruntime en CPU) y deja el modelo versionado.

Uso:
    python exportar_onnx.py                 # exporta clasificador_v1.onnx y segmentacion_v1.onnx (semilla 2024)
    python exportar_onnx.py --reentrenado   # alternativa: exporta los modelos reentrenados sobre train+val
"""
import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import onnxruntime as ort
import pandas as pd
import torch
from PIL import Image

AQUI = Path(__file__).resolve().parent
S2 = AQUI.parent / "Sprint 2 - Entrenamiento"
sys.path.insert(0, str(S2)); sys.path.insert(0, str(AQUI))
from modelos import crear_clasificador, crear_unet  # noqa: E402
from preprocesado import preprocesar  # noqa: E402

SAL2 = S2 / "salida_sprint2"
SAL3 = AQUI / "salida_sprint3"
REGISTRO = AQUI / "modelos"

# modelos desplegados = mejores por validacion del Sprint 2 (semilla 2024)
DESPLIEGUE = {
    "clasificador_v1": dict(pt=SAL2 / "clf_efficientnet_b0_20261023_004900.pt", tarea="clasificacion",
                            construir=lambda ck: crear_clasificador(ck["arquitectura"], preentrenado=False)),
    "segmentacion_v1": dict(pt=SAL2 / "unet_resnet34_20261023_005828.pt", tarea="segmentacion",
                            construir=lambda ck: crear_unet(ck["encoder"], preentrenado=False)),
}
REENTRENADO = {
    "clasificador_final": dict(pt=SAL3 / "clasificador_final.pt", tarea="clasificacion",
                               construir=lambda ck: crear_clasificador(ck["arquitectura"], preentrenado=False)),
    "unet_final": dict(pt=SAL3 / "unet_final.pt", tarea="segmentacion",
                       construir=lambda ck: crear_unet(ck.get("encoder", "resnet34"), preentrenado=False)),
}


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def entradas_reales(n=20):
    raiz = Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))
    man = raiz / "manifest_preparado.csv"
    if man.exists():
        val = pd.read_csv(man).query("particion == 'val'").head(n)
        xs = [preprocesar(Image.open(raiz / r.ruta_imagen))[0] for r in val.itertuples()]
        return np.concatenate(xs, axis=0).astype(np.float32)
    return np.random.randn(n, 3, 256, 256).astype(np.float32)


def exportar(nombre, cfg, device):
    ck = torch.load(cfg["pt"], map_location="cpu", weights_only=False)
    modelo = cfg["construir"](ck).to(device)
    modelo.load_state_dict(ck["modelo"]); modelo.eval()

    REGISTRO.mkdir(exist_ok=True)
    ruta_onnx = REGISTRO / f"{nombre}.onnx"
    entrada = entradas_reales(20)
    ejemplo = torch.from_numpy(entrada).to(device)
    with torch.no_grad():
        salida_torch = modelo(ejemplo).cpu().numpy()
    torch.onnx.export(modelo, ejemplo[:1], str(ruta_onnx), input_names=["imagen"], output_names=["salida"],
                      dynamic_axes={"imagen": {0: "lote"}, "salida": {0: "lote"}}, opset_version=17, dynamo=False)

    sesion = ort.InferenceSession(str(ruta_onnx), providers=["CPUExecutionProvider"])
    salida_onnx = sesion.run(None, {"imagen": entrada})[0]
    max_dif = float(np.abs(salida_torch - salida_onnx).max())
    if cfg["tarea"] == "clasificacion":
        igual = bool((salida_torch.argmax(1) == salida_onnx.argmax(1)).all())
        criterio = "clase identica en 20 imagenes" if igual else "DISCREPANCIA de clase"
    else:
        coincide = float(((salida_torch > 0) == (salida_onnx > 0)).mean())
        igual = coincide > 0.999
        criterio = f"mascara coincide en {coincide*100:.3f}% de pixeles"
    print(f"{nombre}: dif maxima {max_dif:.2e} — {criterio}")
    if not igual or max_dif > 5e-2:
        raise RuntimeError(f"Paridad fallida para {nombre}: {max_dif:.2e}, {criterio}")

    import onnxruntime, torch as _t
    try:
        import segmentation_models_pytorch as smp
        v_smp = smp.__version__
    except Exception:
        v_smp = "n/d"
    tam_mb = sum(p.stat().st_size for p in REGISTRO.glob(f"{nombre}.onnx*")) / 1e6
    tarjeta = dict(
        modelo=nombre, tarea=cfg["tarea"], formato="ONNX opset 17",
        archivo=ruta_onnx.name, tamano_mb=round(tam_mb, 1),
        sha256=sha256(ruta_onnx), fecha_exportacion=datetime.now().strftime("%Y-%m-%d %H:%M"),
        punto_de_control=cfg["pt"].name, semilla=ck.get("semilla", "ver_experimentos"),
        epoca_optima=ck.get("epoca"),
        entrada="float32 [lote,3,256,256] — imagen en gris repetida en 3 canales, normalizacion ImageNet",
        salida=("float32 [lote,4] logits (" + ", ".join(["glioma", "meningioma", "pituitary", "no_tumor"]) + ")")
        if cfg["tarea"] == "clasificacion" else "float32 [lote,1,256,256] logits (sigmoide, umbral 0.5)",
        paridad_pytorch_onnx=f"dif maxima {max_dif:.2e}, {criterio}",
        versiones=dict(torch=_t.__version__, onnxruntime=onnxruntime.__version__, segmentation_models_pytorch=v_smp),
    )
    (REGISTRO / f"{nombre}_tarjeta.json").write_text(json.dumps(tarjeta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {ruta_onnx}  ({tam_mb:.1f} MB)  sha256 {tarjeta['sha256'][:12]}…")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reentrenado", action="store_true", help="exporta la alternativa reentrenada sobre train+val")
    args = ap.parse_args()
    device = torch.device("cpu")
    cjto = REENTRENADO if args.reentrenado else DESPLIEGUE
    for nombre, cfg in cjto.items():
        if cfg["pt"].exists():
            exportar(nombre, cfg, device)
        else:
            print(f"(omitido {nombre}: no existe {cfg['pt']})")
    print("\nListo. Modelos ONNX en:", REGISTRO)


if __name__ == "__main__":
    main()
