"""Evalua un checkpoint en validacion, desglosado por plano de corte y por tipo de archivo
de origen (gris/RGB), para vigilar el posible atajo por procedencia de la imagen (riesgo R09).
Ver docs/TRASPASO_SPRINT2.md, secciones 6.1, 6.2 y 9.

Requiere haber corrido antes (Sprint 1 - Notebooks): python perfil_datos.py

Uso:
    python evaluar_grupos.py --tarea clasificacion --checkpoint salida_sprint2/clf_efficientnet_b0_....pt
    python evaluar_grupos.py --tarea segmentacion --checkpoint salida_sprint2/unet_resnet34_....pt
"""
import argparse
from pathlib import Path

import pandas as pd
import torch

from datos import CLASES, BriscClasificacion, BriscSegmentacion
from experimentos import SALIDA
from metricas import iou_dice, metricas_clasificacion
from modelos import crear_clasificador, crear_unet

AQUI = Path(__file__).resolve().parent
PERFIL = AQUI.parent / "Sprint 1 - Notebooks" / "salida_sprint1" / "perfil_datos" / "perfil_imagenes.csv"


def tabla_modo():
    """archivo (sin extension) -> modo de imagen original (L = gris, RGB)."""
    if not PERFIL.exists():
        raise SystemExit(f"No encuentro {PERFIL}\nEjecuta primero (Sprint 1 - Notebooks): python perfil_datos.py")
    perfil = pd.read_csv(PERFIL)
    perfil["archivo"] = perfil.filename.str.rsplit(".", n=1).str[0]
    return perfil.set_index("archivo")["mode"]


def resumen(df, columnas_metrica, agrupar_por, etiqueta):
    print(f"\n=== Por {etiqueta} ===")
    g = df.groupby(agrupar_por)[columnas_metrica].agg(["mean", "count"])
    print(g.round(4).to_string())
    return g


def evaluar_clasificacion(checkpoint, device):
    ck = torch.load(checkpoint, map_location=device, weights_only=False)
    modelo = crear_clasificador(ck["arquitectura"], preentrenado=False).to(device)
    modelo.load_state_dict(ck["modelo"])
    modelo.eval()

    ds = BriscClasificacion("val", aumentar=False)
    modo = tabla_modo()
    filas = []
    with torch.no_grad():
        for i in range(len(ds)):
            x, y = ds[i]
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = modelo(x.unsqueeze(0).to(device))
            pred = int(logits.argmax(1).item())
            fila = ds.t.iloc[i]
            filas.append(dict(correcto=int(pred == y), real=y, pred=pred,
                               plano=fila.plano, modo=modo.get(fila.archivo, "?")))

    df = pd.DataFrame(filas)
    print(f"accuracy global: {df.correcto.mean():.4f}  (n={len(df)})")
    resumen(df, ["correcto"], "plano", "plano de corte")
    resumen(df, ["correcto"], "modo", "tipo de archivo (origen)")
    for col in ("plano", "modo"):
        for valor, g in df.groupby(col):
            met = metricas_clasificacion(g.real, g.pred, CLASES)
            print(f"  {col}={valor}: recall por clase = " +
                  ", ".join(f"{c} {r:.3f}" for c, r in met["recall_por_clase"].items()))
    return df


def evaluar_segmentacion(checkpoint, device):
    ck = torch.load(checkpoint, map_location=device, weights_only=False)
    modelo = crear_unet(ck["encoder"], preentrenado=False).to(device)
    modelo.load_state_dict(ck["modelo"])
    modelo.eval()

    ds = BriscSegmentacion("val", aumentar=False)
    modo = tabla_modo()
    filas = []
    with torch.no_grad():
        for i in range(len(ds)):
            x, y = ds[i]
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = modelo(x.unsqueeze(0).to(device))
            pred_bin = (torch.sigmoid(logits) > 0.5).float()
            iou, dice = iou_dice(pred_bin, y.unsqueeze(0).to(device))
            fila = ds.t.iloc[i]
            filas.append(dict(iou=float(iou.item()), dice=float(dice.item()),
                               clase=fila.clase, plano=fila.plano, modo=modo.get(fila.archivo, "?")))

    df = pd.DataFrame(filas)
    print(f"IoU global: {df.iou.mean():.4f}  Dice global: {df.dice.mean():.4f}  (n={len(df)})")
    resumen(df, ["iou", "dice"], "clase", "clase")
    resumen(df, ["iou", "dice"], "plano", "plano de corte")
    resumen(df, ["iou", "dice"], "modo", "tipo de archivo (origen)")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tarea", required=True, choices=["clasificacion", "segmentacion"])
    ap.add_argument("--checkpoint", required=True)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = Path(args.checkpoint)
    if args.tarea == "clasificacion":
        df = evaluar_clasificacion(checkpoint, device)
    else:
        df = evaluar_segmentacion(checkpoint, device)

    salida = SALIDA / f"{checkpoint.stem}_por_grupo.csv"
    df.to_csv(salida, index=False)
    print(f"\nDetalle por imagen guardado en: {salida}")


if __name__ == "__main__":
    main()
