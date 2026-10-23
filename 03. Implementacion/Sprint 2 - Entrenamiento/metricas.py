"""Metricas de clasificacion y segmentacion (ver docs/TRASPASO_SPRINT2.md, secciones 6.1 y 6.2)."""
import numpy as np
import torch


def metricas_clasificacion(y_real, y_pred, clases):
    """Accuracy, recall por clase, F1 macro y matriz de confusion."""
    y_real = np.asarray(y_real)
    y_pred = np.asarray(y_pred)
    n = len(clases)
    matriz = np.zeros((n, n), dtype=int)
    for r, p in zip(y_real, y_pred):
        matriz[r, p] += 1

    accuracy = float((y_real == y_pred).mean())
    recall_por_clase, f1_por_clase = {}, []
    for i, c in enumerate(clases):
        tp = matriz[i, i]
        fn = matriz[i, :].sum() - tp
        fp = matriz[:, i].sum() - tp
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        recall_por_clase[c] = recall
        f1_por_clase.append(f1)

    return dict(accuracy=accuracy, recall_por_clase=recall_por_clase,
                f1_macro=float(np.mean(f1_por_clase)), matriz_confusion=matriz)


def iou_dice(pred_bin, real_bin, eps=1e-6):
    """IoU y Dice por imagen (tensores 0/1 de forma [N, 1, H, W]); se promedian fuera de esta funcion."""
    pred = torch.as_tensor(pred_bin).float()
    real = torch.as_tensor(real_bin).float()
    dims = tuple(range(1, pred.ndim))
    inter = (pred * real).sum(dims)
    union = pred.sum(dims) + real.sum(dims) - inter
    iou = (inter + eps) / (union + eps)
    dice = (2 * inter + eps) / (pred.sum(dims) + real.sum(dims) + eps)
    return iou, dice
