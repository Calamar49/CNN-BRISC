"""Reentrena la configuracion ELEGIDA de cada tarea sobre entrenamiento + validacion (5.000 imagenes de
clasificacion; 3.933 con mascara de segmentacion), con el numero de epocas FIJADO en validacion (sin parada
temprana, porque ya no queda validacion para vigilar). Ver docs/TRASPASO_SPRINT2.md seccion 6.4.

Este es el paso previo a HU12: el modelo que se evalua una sola vez en la prueba oficial y el que se despliega
en la aplicacion web es este modelo final reentrenado, no los del Sprint 2.

Numero de epocas fijado = promedio redondeado de la epoca optima de las 3 semillas del Sprint 2 (experimentos.csv):
  - clasificador EfficientNetB0 batch=64: epocas optimas 6/14/10 -> se fija 10.
  - U-Net ResNet34 lr=1e-4:                epocas optimas 28/25/24 -> se fija 26.

Uso:
    python reentrenar_final.py --tarea clasificacion
    python reentrenar_final.py --tarea segmentacion

Guarda el checkpoint final y un JSON de procedencia en salida_sprint3/.
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import ConcatDataset, DataLoader

AQUI = Path(__file__).resolve().parent
S2 = AQUI.parent / "Sprint 2 - Entrenamiento"
sys.path.insert(0, str(S2))

from datos import BriscClasificacion, BriscSegmentacion  # noqa: E402
from modelos import crear_clasificador, crear_unet  # noqa: E402

SALIDA = AQUI / "salida_sprint3"


def fijar_semilla(s):
    import random
    random.seed(s)
    np.random.seed(s)
    torch.manual_seed(s)
    torch.cuda.manual_seed_all(s)


def perdida_bce_dice(logits, real, eps=1e-6):
    bce = F.binary_cross_entropy_with_logits(logits, real)
    pred = torch.sigmoid(logits)
    dims = (1, 2, 3)
    inter = (pred * real).sum(dims)
    dice = (2 * inter + eps) / (pred.sum(dims) + real.sum(dims) + eps)
    return bce + (1 - dice.mean())


def reentrenar_clasificacion(device, epocas, lr, batch, semilla):
    ds = ConcatDataset([BriscClasificacion("train", aumentar=True), BriscClasificacion("val", aumentar=True)])
    loader = DataLoader(ds, batch_size=batch, shuffle=True, num_workers=4, pin_memory=True, persistent_workers=True)
    modelo = crear_clasificador("efficientnet_b0", preentrenado=True).to(device)
    opt = torch.optim.AdamW(modelo.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epocas)
    scaler = torch.amp.GradScaler(device.type, enabled=device.type == "cuda")
    perdida_fn = torch.nn.CrossEntropyLoss()
    print(f"Reentrenando clasificador sobre train+val: {len(ds)} imagenes, {epocas} epocas fijas")
    modelo.train()
    for epoca in range(1, epocas + 1):
        total = 0.0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                perdida = perdida_fn(modelo(x), y)
            scaler.scale(perdida).backward()
            scaler.step(opt)
            scaler.update()
            total += perdida.item() * x.size(0)
        sched.step()
        print(f"  epoca {epoca:02d}/{epocas}  perdida {total / len(ds):.4f}", flush=True)
    return modelo, {"arquitectura": "efficientnet_b0", "batch": batch, "lr": lr}


def reentrenar_segmentacion(device, epocas, lr, batch, semilla):
    ds = ConcatDataset([BriscSegmentacion("train", aumentar=True), BriscSegmentacion("val", aumentar=True)])
    loader = DataLoader(ds, batch_size=batch, shuffle=True, num_workers=4, pin_memory=True, persistent_workers=True)
    modelo = crear_unet("resnet34", preentrenado=True).to(device)
    opt = torch.optim.AdamW(modelo.parameters(), lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epocas)
    scaler = torch.amp.GradScaler(device.type, enabled=device.type == "cuda")
    print(f"Reentrenando U-Net sobre train+val (solo con mascara): {len(ds)} imagenes, {epocas} epocas fijas")
    modelo.train()
    for epoca in range(1, epocas + 1):
        total = 0.0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                perdida = perdida_bce_dice(modelo(x), y)
            scaler.scale(perdida).backward()
            scaler.step(opt)
            scaler.update()
            total += perdida.item() * x.size(0)
        sched.step()
        print(f"  epoca {epoca:02d}/{epocas}  perdida {total / len(ds):.4f}", flush=True)
    return modelo, {"arquitectura": "unet_resnet34", "encoder": "resnet34", "batch": batch, "lr": lr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tarea", required=True, choices=["clasificacion", "segmentacion"])
    ap.add_argument("--epocas", type=int, default=None, help="por defecto 10 (clasif) o 26 (segm)")
    ap.add_argument("--lr", type=float, default=None)
    ap.add_argument("--batch", type=int, default=None)
    ap.add_argument("--semilla", type=int, default=42)
    args = ap.parse_args()

    fijar_semilla(args.semilla)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    SALIDA.mkdir(exist_ok=True)
    print(f"Dispositivo: {device}")

    if args.tarea == "clasificacion":
        epocas = args.epocas or 10
        lr = args.lr or 3e-4
        batch = args.batch or 64
        t0 = time.time()
        modelo, cfg = reentrenar_clasificacion(device, epocas, lr, batch, args.semilla)
        nombre = "clasificador_final"
    else:
        epocas = args.epocas or 26
        lr = args.lr or 1e-4
        batch = args.batch or 8
        t0 = time.time()
        modelo, cfg = reentrenar_segmentacion(device, epocas, lr, batch, args.semilla)
        nombre = "unet_final"

    tiempo_min = (time.time() - t0) / 60
    ruta = SALIDA / f"{nombre}.pt"
    torch.save({"modelo": modelo.state_dict(), **cfg, "epocas": epocas, "semilla": args.semilla,
                "datos": "train+val", "tarea": args.tarea}, ruta)
    proc = dict(nombre=nombre, tarea=args.tarea, fecha=datetime.now().strftime("%Y-%m-%d %H:%M"),
                datos="train+val (entrenamiento + validacion del Sprint 1)", epocas=epocas, lr=lr, batch=batch,
                semilla=args.semilla, optimizador="AdamW", tiempo_min=round(tiempo_min, 1),
                arquitectura=cfg.get("arquitectura"), encoder=cfg.get("encoder"))
    (SALIDA / f"{nombre}_procedencia.json").write_text(json.dumps(proc, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nListo. Checkpoint: {ruta}  ({tiempo_min:.1f} min)")


if __name__ == "__main__":
    main()
