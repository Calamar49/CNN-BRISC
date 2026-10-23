"""Entrena la U-Net de segmentacion (HU05/HU07). Ver docs/TRASPASO_SPRINT2.md, seccion 6.2.

Solo usa imagenes con mascara (3.146 entrenamiento, 787 validacion); sin_tumor queda fuera.

Uso:
    python entrenar_unet.py --encoder resnet34 --epocas 30 --semilla 42

Guarda el mejor checkpoint (segun IoU de validacion), la curva de entrenamiento y unos
ejemplos de mascara predicha frente a la real en salida_sprint2/, y añade una fila a experimentos.csv.
"""
import argparse
import time
from datetime import datetime

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader

from datos import DESVIO, MEDIA, BriscSegmentacion
from experimentos import SALIDA, fijar_semilla, guardar_curva, registrar_experimento
from metricas import iou_dice
from modelos import crear_unet


def perdida_bce_dice(logits, real, eps=1e-6):
    bce = F.binary_cross_entropy_with_logits(logits, real)
    pred = torch.sigmoid(logits)
    dims = (1, 2, 3)
    inter = (pred * real).sum(dims)
    dice = (2 * inter + eps) / (pred.sum(dims) + real.sum(dims) + eps)
    return bce + (1 - dice.mean())


def evaluar(modelo, loader, device):
    modelo.eval()
    ious, dices = [], []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = modelo(x)
            pred_bin = (torch.sigmoid(logits) > 0.5).float()
            iou, dice = iou_dice(pred_bin, y)
            ious.extend(iou.cpu().tolist())
            dices.extend(dice.cpu().tolist())
    return float(np.mean(ious)), float(np.mean(dices))


def guardar_ejemplos(modelo, val_ds, device, exp_id, n=4):
    import matplotlib.pyplot as plt
    modelo.eval()
    idx = np.random.RandomState(42).choice(len(val_ds), size=min(n, len(val_ds)), replace=False)
    fig, ejes = plt.subplots(len(idx), 3, figsize=(9, 3 * len(idx)))
    for fila, i in enumerate(idx):
        x, y = val_ds[i]
        with torch.no_grad(), torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
            pred = torch.sigmoid(modelo(x.unsqueeze(0).to(device)))[0, 0].cpu()
        img = (x[0] * DESVIO[0, 0, 0] + MEDIA[0, 0, 0]).clamp(0, 1).numpy()
        ejes[fila, 0].imshow(img, cmap="gray"); ejes[fila, 0].set_title("imagen"); ejes[fila, 0].axis("off")
        ejes[fila, 1].imshow(y[0].numpy(), cmap="gray"); ejes[fila, 1].set_title("mascara real"); ejes[fila, 1].axis("off")
        ejes[fila, 2].imshow((pred > 0.5).numpy(), cmap="gray"); ejes[fila, 2].set_title("mascara predicha"); ejes[fila, 2].axis("off")
    fig.tight_layout()
    fig.savefig(SALIDA / f"{exp_id}_ejemplos.png", dpi=120)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--encoder", default="resnet34")
    ap.add_argument("--sin-preentrenado", dest="preentrenado", action="store_false", default=True)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--epocas", type=int, default=30)
    ap.add_argument("--paciencia", type=int, default=5)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--sin-aumento", dest="aumento", action="store_false", default=True)
    ap.add_argument("--historia", default="HU07")
    ap.add_argument("--notas", default="")
    args = ap.parse_args()

    fijar_semilla(args.semilla)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    SALIDA.mkdir(exist_ok=True)
    print(f"Dispositivo: {device}")

    train_ds = BriscSegmentacion("train", aumentar=args.aumento)
    val_ds = BriscSegmentacion("val", aumentar=False)
    print(f"Entrenamiento: {len(train_ds)}  Validacion: {len(val_ds)}")
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=4, pin_memory=True,
                               persistent_workers=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=2, pin_memory=True,
                             persistent_workers=True)

    modelo = crear_unet(args.encoder, preentrenado=args.preentrenado).to(device)
    opt = torch.optim.AdamW(modelo.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epocas)
    scaler = torch.amp.GradScaler(device.type, enabled=device.type == "cuda")

    exp_id = f"unet_{args.encoder}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    checkpoint = SALIDA / f"{exp_id}.pt"
    curva, mejor_iou, mejor_epoca, sin_mejora, epoca = [], -1.0, 0, 0, 0
    t0 = time.time()

    for epoca in range(1, args.epocas + 1):
        modelo.train()
        perdida_total = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = modelo(x)
                perdida = perdida_bce_dice(logits, y)
            scaler.scale(perdida).backward()
            scaler.step(opt)
            scaler.update()
            perdida_total += perdida.item() * x.size(0)
        sched.step()
        perdida_media = perdida_total / len(train_ds)

        val_iou, val_dice = evaluar(modelo, val_loader, device)
        curva.append(dict(epoca=epoca, perdida_train=perdida_media, val_iou=val_iou, val_dice=val_dice))
        print(f"epoca {epoca:02d}  perdida {perdida_media:.4f}  val_iou {val_iou:.4f}  val_dice {val_dice:.4f}")

        if val_iou > mejor_iou:
            mejor_iou, mejor_epoca, sin_mejora = val_iou, epoca, 0
            torch.save({"modelo": modelo.state_dict(), "encoder": args.encoder, "epoca": epoca,
                        "val_iou": val_iou, "val_dice": val_dice}, checkpoint)
        else:
            sin_mejora += 1
            if sin_mejora >= args.paciencia:
                print(f"parada temprana en la epoca {epoca} (sin mejora por {args.paciencia} epocas)")
                break

    tiempo_min = (time.time() - t0) / 60
    guardar_curva(curva, SALIDA / f"{exp_id}_curva.csv")

    mejor = torch.load(checkpoint, map_location=device, weights_only=False)
    modelo.load_state_dict(mejor["modelo"])
    guardar_ejemplos(modelo, val_ds, device, exp_id)

    registrar_experimento(dict(
        id=exp_id, fecha=datetime.now().strftime("%Y-%m-%d"), historia=args.historia, tarea="segmentacion",
        arquitectura=f"unet_{args.encoder}", preentrenado=args.preentrenado, tamano_imagen=256, batch=args.batch,
        lr=args.lr, optimizador="AdamW", perdida="BCE+Dice", epocas=epoca, epoca_optima=mejor_epoca,
        aumento=args.aumento, semilla=args.semilla, val_accuracy="", val_recall_por_clase="", val_f1_macro="",
        val_iou=round(mejor["val_iou"], 4), val_dice=round(mejor["val_dice"], 4), tiempo_min=round(tiempo_min, 1),
        checkpoint=str(checkpoint.relative_to(checkpoint.parents[1])), notas=args.notas,
    ))
    print(f"\nListo. Mejor epoca: {mejor_epoca}  val_iou: {mejor_iou:.4f}")
    print(f"Checkpoint: {checkpoint}\nRegistrado en: experimentos.csv")


if __name__ == "__main__":
    main()
