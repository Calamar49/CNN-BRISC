"""Exporta los modelos finales reentrenados (salida_sprint3/*.pt) a ONNX, en la carpeta registro de modelos
(modelos/), y verifica que la salida de ONNX coincide con la de PyTorch (paridad numerica). HU13/HU14.

ONNX permite servir el modelo sin PyTorch (la aplicacion web usa onnxruntime, mas liviano) y deja el modelo en
un formato estandar y versionado para el registro de modelos (MLOps basico, HU14).

Uso:
    python exportar_onnx.py          # exporta clasificador y U-Net
    python exportar_onnx.py --tarea clasificacion
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import os

import numpy as np
import onnxruntime as ort
import pandas as pd
import torch
from PIL import Image

AQUI = Path(__file__).resolve().parent
S2 = AQUI.parent / "Sprint 2 - Entrenamiento"
sys.path.insert(0, str(S2))
from modelos import crear_clasificador, crear_unet  # noqa: E402

SALIDA = AQUI / "salida_sprint3"
REGISTRO = AQUI / "modelos"
sys.path.insert(0, str(AQUI))
from preprocesado import CLASES, preprocesar  # noqa: E402


def entradas_reales(n=5):
    """Unas imagenes reales de prueba, preprocesadas (en-distribucion), para medir la paridad de forma
    representativa; si no esta el dataset, cae a ruido aleatorio."""
    raiz = Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))
    man = raiz / "manifest_preparado.csv"
    if man.exists():
        test = pd.read_csv(man).query("particion == 'test'").head(n)
        xs = []
        for r in test.itertuples():
            with Image.open(raiz / r.ruta_imagen) as im:
                xs.append(preprocesar(im)[0])
        return np.concatenate(xs, axis=0).astype(np.float32)
    return np.random.randn(n, 3, 256, 256).astype(np.float32)


def exportar(nombre, construir, ruta_pt, device):
    ck = torch.load(ruta_pt, map_location="cpu", weights_only=False)
    modelo = construir().to(device)
    modelo.load_state_dict(ck["modelo"])
    modelo.eval()

    REGISTRO.mkdir(exist_ok=True)
    ruta_onnx = REGISTRO / f"{nombre}.onnx"
    entrada = entradas_reales(5)
    ejemplo = torch.from_numpy(entrada).to(device)

    # salida de referencia en modo eval ANTES de exportar (la exportacion puede dejar el modelo en train)
    with torch.no_grad():
        salida_torch = modelo(ejemplo).cpu().numpy()

    torch.onnx.export(
        modelo, ejemplo[:1], str(ruta_onnx), input_names=["entrada"], output_names=["salida"],
        dynamic_axes={"entrada": {0: "lote"}, "salida": {0: "lote"}}, opset_version=17,
        dynamo=False,  # exportador clasico (TorchScript): paridad numerica estricta
    )

    sesion = ort.InferenceSession(str(ruta_onnx), providers=["CPUExecutionProvider"])
    salida_onnx = sesion.run(None, {"entrada": entrada})[0]
    max_dif = float(np.abs(salida_torch - salida_onnx).max())
    # criterio funcional: en clasificacion, la clase predicha (argmax) debe coincidir en las 5 imagenes;
    # en segmentacion, la decision de mascara (umbral 0.5) debe coincidir en casi todos los pixeles.
    if salida_onnx.ndim == 2:
        igual = bool((salida_torch.argmax(1) == salida_onnx.argmax(1)).all())
        criterio = "clase predicha identica en las 5 imagenes" if igual else "DISCREPANCIA en la clase predicha"
    else:
        coincide = float(((salida_torch > 0) == (salida_onnx > 0)).mean())
        igual = coincide > 0.999
        criterio = f"decision de mascara coincide en {coincide*100:.3f}% de los pixeles"
    print(f"{nombre}: forma {salida_onnx.shape}, dif. maxima PyTorch vs ONNX = {max_dif:.2e} — {criterio}")
    if not igual or max_dif > 5e-2:
        raise RuntimeError(f"La paridad fallo para {nombre}: dif {max_dif:.2e}, {criterio}")

    tam_mb = ruta_onnx.stat().st_size / 1e6
    proc_path = SALIDA / f"{nombre}_procedencia.json"
    proc = json.loads(proc_path.read_text(encoding="utf-8")) if proc_path.exists() else {}
    tarjeta = dict(
        modelo=nombre, formato="ONNX opset 17", archivo=ruta_onnx.name, tamano_mb=round(tam_mb, 1),
        fecha_exportacion=datetime.now().strftime("%Y-%m-%d %H:%M"),
        entrada="float32 [lote, 3, 256, 256] — imagen en gris repetida en 3 canales, normalizacion de ImageNet",
        salida=("float32 [lote, 4] logits de clase (" + ", ".join(CLASES) + ")") if "clasificador" in nombre
        else "float32 [lote, 1, 256, 256] logits de mascara (aplicar sigmoide y umbral 0.5)",
        paridad_pytorch_onnx=f"diferencia maxima {max_dif:.2e}", entrenamiento=proc,
    )
    (REGISTRO / f"{nombre}_tarjeta.json").write_text(json.dumps(tarjeta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  -> {ruta_onnx}  ({tam_mb:.1f} MB)  + tarjeta de modelo")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tarea", default="ambas", choices=["ambas", "clasificacion", "segmentacion"])
    args = ap.parse_args()
    device = torch.device("cpu")  # exportacion en CPU: la paridad se mide ahi mismo

    if args.tarea in ("ambas", "clasificacion"):
        exportar("clasificador_final", lambda: crear_clasificador("efficientnet_b0", preentrenado=False),
                 SALIDA / "clasificador_final.pt", device)
    if args.tarea in ("ambas", "segmentacion"):
        exportar("unet_final", lambda: crear_unet("resnet34", preentrenado=False),
                 SALIDA / "unet_final.pt", device)
    print("\nListo. Modelos ONNX en:", REGISTRO)


if __name__ == "__main__":
    main()
