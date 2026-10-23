"""Entrena el clasificador de tipo de tumor, 4 clases (HU05/HU06). Ver docs/TRASPASO_SPRINT2.md, seccion 6.1.

Uso:
    python entrenar_clasificador.py --arquitectura efficientnet_b0 --epocas 20 --semilla 42
    python entrenar_clasificador.py --arquitectura resnet50 --epocas 20 --semilla 42

Guarda el mejor checkpoint (segun recall medio de validacion) y la curva de entrenamiento en
salida_sprint2/, y añade una fila a experimentos.csv.
"""
import argparse
import json
import time
from datetime import datetime

import numpy as np
import torch
from torch.utils.data import DataLoader

from datos import CLASES, BriscClasificacion
from experimentos import SALIDA, fijar_semilla, guardar_curva, registrar_experimento
from metricas import metricas_clasificacion
from modelos import crear_clasificador


def evaluar(modelo, loader, device):
    modelo.eval()
    y_real, y_pred = [], []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = modelo(x)
            y_pred.extend(logits.argmax(1).cpu().tolist())
            y_real.extend(y.tolist())
    return metricas_clasificacion(y_real, y_pred, CLASES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arquitectura", default="efficientnet_b0", choices=["efficientnet_b0", "resnet50"])
    ap.add_argument("--sin-preentrenado", dest="preentrenado", action="store_false", default=True)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--epocas", type=int, default=20)
    ap.add_argument("--paciencia", type=int, default=5)
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--sin-aumento", dest="aumento", action="store_false", default=True)
    ap.add_argument("--historia", default="HU06")
    ap.add_argument("--notas", default="")
    args = ap.parse_args()

    fijar_semilla(args.semilla)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    SALIDA.mkdir(exist_ok=True)
    print(f"Dispositivo: {device}")

    train_ds = BriscClasificacion("train", aumentar=args.aumento)
    val_ds = BriscClasificacion("val", aumentar=False)
    print(f"Entrenamiento: {len(train_ds)}  Validacion: {len(val_ds)}")
    train_loader = DataLoader(train_ds, batch_size=args.batch, shuffle=True, num_workers=4, pin_memory=True,
                               persistent_workers=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch, shuffle=False, num_workers=2, pin_memory=True,
                             persistent_workers=True)

    modelo = crear_clasificador(args.arquitectura, preentrenado=args.preentrenado).to(device)
    opt = torch.optim.AdamW(modelo.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epocas)
    scaler = torch.amp.GradScaler(device.type, enabled=device.type == "cuda")
    perdida_fn = torch.nn.CrossEntropyLoss()

    exp_id = f"clf_{args.arquitectura}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    checkpoint = SALIDA / f"{exp_id}.pt"
    curva, mejor_recall, mejor_epoca, sin_mejora, epoca = [], -1.0, 0, 0, 0
    t0 = time.time()

    for epoca in range(1, args.epocas + 1):
        modelo.train()
        perdida_total = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = modelo(x)
                perdida = perdida_fn(logits, y)
            scaler.scale(perdida).backward()
            scaler.step(opt)
            scaler.update()
            perdida_total += perdida.item() * x.size(0)
        sched.step()
        perdida_media = perdida_total / len(train_ds)

        met = evaluar(modelo, val_loader, device)
        recall_medio = float(np.mean(list(met["recall_por_clase"].values())))
        curva.append(dict(epoca=epoca, perdida_train=perdida_media, val_accuracy=met["accuracy"],
                           val_recall_medio=recall_medio, val_f1_macro=met["f1_macro"]))
        print(f"epoca {epoca:02d}  perdida {perdida_media:.4f}  val_acc {met['accuracy']:.4f}  "
              f"val_recall_medio {recall_medio:.4f}  val_f1_macro {met['f1_macro']:.4f}")

        if recall_medio > mejor_recall:
            mejor_recall, mejor_epoca, sin_mejora = recall_medio, epoca, 0
            torch.save({"modelo": modelo.state_dict(), "arquitectura": args.arquitectura, "epoca": epoca,
                        "metricas": met}, checkpoint)
        else:
            sin_mejora += 1
            if sin_mejora >= args.paciencia:
                print(f"parada temprana en la epoca {epoca} (sin mejora por {args.paciencia} epocas)")
                break

    tiempo_min = (time.time() - t0) / 60
    guardar_curva(curva, SALIDA / f"{exp_id}_curva.csv")

    mejor = torch.load(checkpoint, map_location=device, weights_only=False)
    met_final = mejor["metricas"]
    registrar_experimento(dict(
        id=exp_id, fecha=datetime.now().strftime("%Y-%m-%d"), historia=args.historia, tarea="clasificacion",
        arquitectura=args.arquitectura, preentrenado=args.preentrenado, tamano_imagen=256, batch=args.batch,
        lr=args.lr, optimizador="AdamW", perdida="CrossEntropy", epocas=epoca, epoca_optima=mejor_epoca,
        aumento=args.aumento, semilla=args.semilla, val_accuracy=round(met_final["accuracy"], 4),
        val_recall_por_clase=json.dumps({k: round(v, 4) for k, v in met_final["recall_por_clase"].items()}),
        val_f1_macro=round(met_final["f1_macro"], 4), val_iou="", val_dice="", tiempo_min=round(tiempo_min, 1),
        checkpoint=str(checkpoint.relative_to(checkpoint.parents[1])), notas=args.notas,
    ))
    print(f"\nListo. Mejor epoca: {mejor_epoca}  val_recall_medio: {mejor_recall:.4f}")
    print(f"Checkpoint: {checkpoint}\nRegistrado en: experimentos.csv")


if __name__ == "__main__":
    main()
