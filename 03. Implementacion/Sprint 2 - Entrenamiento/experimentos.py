"""Columnas y utilidades comunes para experimentos.csv (ver docs/TRASPASO_SPRINT2.md, seccion 6.5)."""
import csv
import random
from pathlib import Path

import numpy as np
import torch

AQUI = Path(__file__).resolve().parent
SALIDA = AQUI / "salida_sprint2"
EXPERIMENTOS = AQUI / "experimentos.csv"
COLUMNAS = ["id", "fecha", "historia", "tarea", "arquitectura", "preentrenado", "tamano_imagen", "batch", "lr",
            "optimizador", "perdida", "epocas", "epoca_optima", "aumento", "semilla", "val_accuracy",
            "val_recall_por_clase", "val_f1_macro", "val_iou", "val_dice", "tiempo_min", "checkpoint", "notas"]


def fijar_semilla(semilla):
    random.seed(semilla)
    np.random.seed(semilla)
    torch.manual_seed(semilla)
    torch.cuda.manual_seed_all(semilla)


def registrar_experimento(fila):
    nuevo = not EXPERIMENTOS.exists()
    with open(EXPERIMENTOS, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        if nuevo:
            w.writeheader()
        w.writerow(fila)


def guardar_curva(curva, ruta):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(curva[0].keys()))
        w.writeheader()
        w.writerows(curva)
