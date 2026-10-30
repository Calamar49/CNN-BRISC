# -*- coding: utf-8 -*-
"""Graficos del informe del Sprint 3, a partir de datos reales de la evaluacion unica sobre la prueba oficial
(salida_sprint3/evaluacion_prueba.json). No inventa datos. Mismo estilo que gen_figs_sprint2.py.

Reune en herramientas/figs_sprint3/:
  - matriz de confusion en prueba, IoU por clase en prueba (copiadas de salida_sprint3/ que las genero evaluar_prueba.py),
  - validacion (Sprint 2) vs prueba oficial (HU12) para las dos tareas,
  - desempeno por plano de corte y por tipo de archivo en la prueba (riesgo R09),
  - las capturas reales de la aplicacion web (de herramientas/capturas_app/).
"""
import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_AQUI = _P = Path(__file__).resolve().parent
_RAIZ = _AQUI.parent
S3 = _RAIZ / "03. Implementacion" / "Sprint 3 - Evaluacion y despliegue"
SAL3 = S3 / "salida_sprint3"
CAPT = _AQUI / "capturas_app"
OUT = _AQUI / "figs_sprint3"
OUT.mkdir(exist_ok=True)

NAVY, BLUE, TEAL, GREEN, GRAY = "#1F3864", "#5B84B1", "#2B7A8B", "#8FB89A", "#9AA5B1"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
CLASES_ES = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Hipófisis", "no_tumor": "Sin tumor"}
PLANO_ES = {"ax": "Axial", "co": "Coronal", "sa": "Sagital"}


def _datos():
    return json.loads((SAL3 / "evaluacion_prueba.json").read_text(encoding="utf-8"))


def copiar_existentes():
    for n in ("prueba_matriz_confusion.png", "prueba_iou_por_clase.png"):
        if (SAL3 / n).exists():
            shutil.copy(SAL3 / n, OUT / n)
    for n in ("app_vacio.jpg", "app_glioma.jpg", "app_meningioma.jpg", "app_sin_tumor.jpg"):
        if (CAPT / n).exists():
            shutil.copy(CAPT / n, OUT / n)


def fig_val_vs_prueba(d):
    """Validacion (Sprint 2, promedio 3 semillas) vs prueba oficial (HU12). Las de validacion son del README S2."""
    clf = d["clasificacion"]; seg = d["segmentacion"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))

    etq = ["Accuracy", "Recall medio", "F1 macro"]
    recall_medio_prueba = float(np.mean(list(clf["recall_por_clase"].values())))
    val = [None, 99.57, None]   # solo el recall medio tiene promedio multi-semilla en validacion
    prueba = [clf["accuracy"] * 100, recall_medio_prueba * 100, clf["f1_macro"] * 100]
    x = np.arange(len(etq)); w = 0.38
    ax[0].bar(x - w / 2, [v if v is not None else 0 for v in val], w, color=GRAY, label="Validación (Sprint 2)")
    ax[0].bar(x + w / 2, prueba, w, color=NAVY, label="Prueba oficial (HU12)")
    ax[0].axhline(95, color=TEAL, ls="--", lw=1, label="Meta accuracy 95%")
    for i, v in enumerate(prueba):
        ax[0].text(i + w / 2, v + 0.2, f"{v:.2f}", ha="center", fontsize=8)
    if val[1] is not None:
        ax[0].text(1 - w / 2, val[1] + 0.2, f"{val[1]:.2f}", ha="center", fontsize=8)
    ax[0].set_xticks(x); ax[0].set_xticklabels(etq); ax[0].set_ylim(90, 101)
    ax[0].set_ylabel("%"); ax[0].set_title("Clasificador — validación vs prueba oficial")
    ax[0].legend(frameon=False, fontsize=8)

    etq2 = ["IoU", "Dice"]
    val2 = [80.12, None]; prueba2 = [seg["iou"] * 100, seg["dice"] * 100]
    x2 = np.arange(len(etq2))
    ax[1].bar(x2 - w / 2, [v if v is not None else 0 for v in val2], w, color=GRAY, label="Validación (Sprint 2)")
    ax[1].bar(x2 + w / 2, prueba2, w, color=NAVY, label="Prueba oficial (HU12)")
    ax[1].axhline(70, color=TEAL, ls="--", lw=1, label="Meta IoU 70%")
    for i, v in enumerate(prueba2):
        ax[1].text(i + w / 2, v + 0.4, f"{v:.2f}", ha="center", fontsize=8)
    ax[1].text(0 - w / 2, val2[0] + 0.4, f"{val2[0]:.2f}", ha="center", fontsize=8)
    ax[1].set_xticks(x2); ax[1].set_xticklabels(etq2); ax[1].set_ylim(60, 95)
    ax[1].set_ylabel("%"); ax[1].set_title("U-Net — validación vs prueba oficial")
    ax[1].legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "val_vs_prueba.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_recall_por_clase_prueba(d):
    clf = d["clasificacion"]
    clases = list(clf["recall_por_clase"].keys())
    vals = [clf["recall_por_clase"][c] * 100 for c in clases]
    fig, ax = plt.subplots(figsize=(6.4, 4))
    cols = [NAVY if v >= 90 else "#b5651d" for v in vals]
    ax.bar([CLASES_ES[c] for c in clases], vals, color=cols)
    ax.axhline(90, color=TEAL, ls="--", lw=1, label="Meta recall 90%")
    for i, v in enumerate(vals):
        ax.text(i, v + 0.2, f"{v:.1f}", ha="center", fontsize=9)
    ax.set_ylim(90, 101); ax.set_ylabel("Recall (%)")
    ax.set_title("Clasificador — recall por clase en la prueba oficial", fontsize=11)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(OUT / "prueba_recall_por_clase.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_por_plano_modo(d):
    seg = d["segmentacion"]; clf = d["clasificacion"]
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.9))
    # clasificacion por tipo de archivo
    modo = clf["accuracy_por_modo"]
    etq = list(modo.keys()); vals = [modo[k]["valor"] * 100 for k in etq]
    ax[0].bar(etq, vals, color=[TEAL, BLUE][:len(etq)])
    for i, (k, v) in enumerate(zip(etq, vals)):
        ax[0].text(i, v + 0.1, f"{v:.2f}\n(n={modo[k]['n']})", ha="center", fontsize=8)
    ax[0].set_ylim(95, 100.5); ax[0].set_ylabel("Accuracy (%)")
    ax[0].set_title("Clasificador: accuracy por tipo de archivo (prueba)")
    # segmentacion por tipo de archivo
    modos = seg["iou_por_modo"]
    etq2 = list(modos.keys()); vals2 = [modos[k]["valor"] * 100 for k in etq2]
    ax[1].bar(etq2, vals2, color=[TEAL, BLUE][:len(etq2)])
    for i, (k, v) in enumerate(zip(etq2, vals2)):
        ax[1].text(i, v + 0.5, f"{v:.1f}\n(n={modos[k]['n']})", ha="center", fontsize=8)
    ax[1].set_ylim(60, 92); ax[1].set_ylabel("IoU (%)")
    ax[1].set_title("U-Net: IoU por tipo de archivo (prueba, riesgo R09)")
    fig.tight_layout(); fig.savefig(OUT / "prueba_por_modo.png", dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    d = _datos()
    copiar_existentes()
    fig_val_vs_prueba(d)
    fig_recall_por_clase_prueba(d)
    fig_por_plano_modo(d)
    print("Listo:", OUT)
