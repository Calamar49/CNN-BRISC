# -*- coding: utf-8 -*-
"""Figuras del informe/presentacion del Sprint 3, a partir de datos reales de la evaluacion unica sobre la prueba
oficial (salida_sprint3/evaluacion_prueba.json, protocolo de 6 checkpoints del plan). No inventa datos.

Reune en herramientas/figs_sprint3/:
  - validacion (Sprint 2) vs prueba oficial (HU12), por tarea;
  - matriz de confusion, IoU por clase, ejemplos de aciertos/errores (copiadas de salida_sprint3);
  - recall por clase y desglose por tipo de archivo (R09) en la prueba;
  - resultado por semilla (3 semillas) y efecto del subconjunto sin vecino cercano;
  - las capturas reales de la aplicacion clinica (herramientas/capturas_app/).
"""
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_AQUI = Path(__file__).resolve().parent
_RAIZ = _AQUI.parent
S3 = _RAIZ / "03. Implementacion" / "Sprint 3 - Evaluacion y despliegue"
SAL3 = S3 / "salida_sprint3"
CAPT = _AQUI / "capturas_app"
OUT = _AQUI / "figs_sprint3"
OUT.mkdir(exist_ok=True)

NAVY, BLUE, TEAL, GREEN, GRAY = "#1F3864", "#5B84B1", "#2B7A8B", "#8FB89A", "#9AA5B1"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
CLASES_ES = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Hipófisis", "no_tumor": "Sin tumor"}

VAL_RECALL, VAL_IOU = 99.57, 80.12  # validacion Sprint 2 (promedio 3 semillas), del README del Sprint 2


def datos():
    return json.loads((SAL3 / "evaluacion_prueba.json").read_text(encoding="utf-8"))


def copiar():
    for n in ("prueba_matriz_confusion.png", "prueba_iou_por_clase.png",
              "prueba_ejemplos_clasificacion.png", "prueba_ejemplos_segmentacion.png"):
        if (SAL3 / n).exists():
            shutil.copy(SAL3 / n, OUT / n)
    for p in CAPT.glob("app_*.jpg"):
        shutil.copy(p, OUT / p.name)


def fig_val_vs_prueba(d):
    c, s = d["clasificacion"], d["segmentacion"]
    dc, ds = c["desplegado"], s["desplegado"]
    recall_medio = float(np.mean(list(dc["recall_por_clase"].values()))) * 100
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    etq = ["Accuracy", "Recall medio", "F1 macro"]
    val = [None, VAL_RECALL, None]
    prueba = [dc["accuracy"] * 100, recall_medio, dc["f1_macro"] * 100]
    x = np.arange(len(etq)); w = 0.38
    ax[0].bar(x - w / 2, [v or 0 for v in val], w, color=GRAY, label="Validación (Sprint 2)")
    ax[0].bar(x + w / 2, prueba, w, color=NAVY, label="Prueba oficial (HU12)")
    ax[0].axhline(95, color=TEAL, ls="--", lw=1, label="Meta 95%")
    for i, v in enumerate(prueba):
        ax[0].text(i + w / 2, v + 0.15, f"{v:.2f}", ha="center", fontsize=8)
    ax[0].text(1 - w / 2, VAL_RECALL + 0.15, f"{VAL_RECALL:.2f}", ha="center", fontsize=8)
    ax[0].set_xticks(x); ax[0].set_xticklabels(etq); ax[0].set_ylim(90, 101); ax[0].set_ylabel("%")
    ax[0].set_title("Clasificador — validación vs prueba oficial"); ax[0].legend(frameon=False, fontsize=8)

    etq2 = ["IoU", "Dice"]; val2 = [VAL_IOU, None]; prueba2 = [ds["iou"] * 100, ds["dice"] * 100]
    x2 = np.arange(len(etq2))
    ax[1].bar(x2 - w / 2, [v or 0 for v in val2], w, color=GRAY, label="Validación (Sprint 2)")
    ax[1].bar(x2 + w / 2, prueba2, w, color=NAVY, label="Prueba oficial (HU12)")
    ax[1].axhline(70, color=TEAL, ls="--", lw=1, label="Meta 70%")
    for i, v in enumerate(prueba2):
        ax[1].text(i + w / 2, v + 0.4, f"{v:.2f}", ha="center", fontsize=8)
    ax[1].text(0 - w / 2, VAL_IOU + 0.4, f"{VAL_IOU:.2f}", ha="center", fontsize=8)
    ax[1].set_xticks(x2); ax[1].set_xticklabels(etq2); ax[1].set_ylim(60, 95); ax[1].set_ylabel("%")
    ax[1].set_title("U-Net — validación vs prueba oficial"); ax[1].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "val_vs_prueba.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_recall_por_clase(d):
    dc = d["clasificacion"]["desplegado"]
    clases = list(dc["recall_por_clase"].keys()); vals = [dc["recall_por_clase"][c] * 100 for c in clases]
    fig, ax = plt.subplots(figsize=(6.4, 4))
    ax.bar([CLASES_ES[c] for c in clases], vals, color=[NAVY if v >= 90 else "#b5651d" for v in vals])
    ax.axhline(90, color=TEAL, ls="--", lw=1, label="Meta 90%")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.15, f"{v:.1f}", ha="center", fontsize=9)
    ax.set_ylim(90, 101); ax.set_ylabel("Recall (%)")
    ax.set_title("Clasificador — recall por clase en la prueba oficial", fontsize=11); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "prueba_recall_por_clase.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_por_modo(d):
    c, s = d["clasificacion"], d["segmentacion"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.9))
    modo = c["accuracy_por_modo"]; etq = list(modo.keys()); vals = [modo[k]["valor"] * 100 for k in etq]
    ax[0].bar(etq, vals, color=[TEAL, BLUE][:len(etq)])
    for i, k in enumerate(etq):
        ax[0].text(i, vals[i] + 0.08, f"{vals[i]:.2f}\n(n={modo[k]['n']})", ha="center", fontsize=8)
    ax[0].set_ylim(95, 100.4); ax[0].set_ylabel("Accuracy (%)")
    ax[0].set_title("Clasificador: accuracy por tipo de archivo (prueba)")
    modos = s["desplegado"]["iou_por_modo"]; etq2 = list(modos.keys()); vals2 = [modos[k]["valor"] * 100 for k in etq2]
    ax[1].bar(etq2, vals2, color=[TEAL, BLUE][:len(etq2)])
    for i, k in enumerate(etq2):
        ax[1].text(i, vals2[i] + 0.5, f"{vals2[i]:.1f}\n(n={modos[k]['n']})", ha="center", fontsize=8)
    ax[1].set_ylim(60, 92); ax[1].set_ylabel("IoU (%)")
    ax[1].set_title("U-Net: IoU por tipo de archivo (prueba, R09)")
    fig.tight_layout(); fig.savefig(OUT / "prueba_por_modo.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_semillas_y_vecino(d):
    c, s = d["clasificacion"], d["segmentacion"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    # 3 semillas
    semillas = ["42", "123", "2024"]
    acc = [c["por_semilla"][k]["accuracy"] * 100 for k in semillas]
    iou = [s["por_semilla"][k]["iou"] * 100 for k in semillas]
    x = np.arange(len(semillas)); w = 0.38
    ax[0].bar(x - w / 2, acc, w, color=NAVY, label="Accuracy clasif.")
    ax[0].bar(x + w / 2, iou, w, color=TEAL, label="IoU U-Net")
    for i in range(3):
        ax[0].text(i - w / 2, acc[i] + 0.3, f"{acc[i]:.2f}", ha="center", fontsize=8)
        ax[0].text(i + w / 2, iou[i] + 0.3, f"{iou[i]:.2f}", ha="center", fontsize=8)
    ax[0].set_xticks(x); ax[0].set_xticklabels(["semilla " + s_ for s_ in semillas]); ax[0].set_ylim(60, 102)
    ax[0].set_ylabel("%"); ax[0].set_title("Prueba oficial por semilla (desplegada: 2024)")
    ax[0].legend(frameon=False, fontsize=8)
    # con vs sin vecino cercano
    etq = ["Accuracy\nclasif.", "IoU\nU-Net"]
    todo = [c["desplegado"]["accuracy"] * 100, s["desplegado"]["iou"] * 100]
    sin = [c["accuracy_sin_vecino"] * 100, s["iou_sin_vecino"] * 100]
    x2 = np.arange(len(etq))
    ax[1].bar(x2 - w / 2, todo, w, color=NAVY, label=f"Todas ({c.get('n_sin_vecino','')}+)")
    ax[1].bar(x2 + w / 2, sin, w, color=GRAY, label="Sin vecino cercano")
    for i in range(2):
        ax[1].text(i - w / 2, todo[i] + 0.4, f"{todo[i]:.2f}", ha="center", fontsize=8)
        ax[1].text(i + w / 2, sin[i] + 0.4, f"{sin[i]:.2f}", ha="center", fontsize=8)
    ax[1].set_xticks(x2); ax[1].set_xticklabels(etq); ax[1].set_ylim(60, 102); ax[1].set_ylabel("%")
    ax[1].set_title(f"Efecto de la fuga ({d['imagenes_con_vecino_cercano']} imágenes con vecino)")
    ax[1].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "prueba_semillas_vecino.png", dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    d = datos()
    copiar()
    fig_val_vs_prueba(d)
    fig_recall_por_clase(d)
    fig_por_modo(d)
    fig_semillas_y_vecino(d)
    print("Listo:", OUT)
