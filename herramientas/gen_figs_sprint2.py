# -*- coding: utf-8 -*-
"""Graficos del informe del Sprint 2, a partir de datos reales guardados por los scripts de entrenamiento
(curvas de entrenamiento, matriz de confusion, comparacion de configuraciones HU08). No usa datos inventados:
todo sale de salida_sprint2/*.csv (ver "03. Implementacion/Sprint 2 - Entrenamiento/").
"""
from pathlib import Path as _P

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_AQUI = _P(__file__).resolve().parent
_RAIZ = _AQUI.parent
S2 = _RAIZ / "03. Implementacion" / "Sprint 2 - Entrenamiento"
SAL = S2 / "salida_sprint2"
OUT = _AQUI / "figs_sprint2"
OUT.mkdir(exist_ok=True)

NAVY, BLUE, TEAL, GREEN, GRAY = "#1F3864", "#5B84B1", "#2B7A8B", "#8FB89A", "#9AA5B1"
PALETA = [NAVY, BLUE, TEAL, GREEN, GRAY]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                      "font.family": "DejaVu Sans", "axes.prop_cycle": plt.cycler(color=PALETA)})
CLASES = ["glioma", "meningioma", "pituitary", "no_tumor"]
ES = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Hipófisis", "no_tumor": "Sin tumor"}

# checkpoints ganadores (semilla 42), ver experimentos.csv
CLF_ID = "clf_efficientnet_b0_20261023_002839"      # batch=64, HU08
UNET_ID = "unet_resnet34_20261023_002334"            # lr=1e-4, HU08


def fig_curva_clasificador():
    df = pd.read_csv(SAL / f"{CLF_ID}_curva.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    ax[0].plot(df.epoca, df.perdida_train, color=NAVY, marker="o", ms=3)
    ax[0].set_title("Pérdida de entrenamiento")
    ax[0].set_xlabel("Época"); ax[0].set_ylabel("Pérdida (CrossEntropy)")
    ax[1].plot(df.epoca, df.val_accuracy * 100, color=BLUE, marker="o", ms=3, label="Accuracy")
    ax[1].plot(df.epoca, df.val_recall_medio * 100, color=TEAL, marker="s", ms=3, label="Recall medio")
    ax[1].set_title("Validación")
    ax[1].set_xlabel("Época"); ax[1].set_ylabel("%")
    ax[1].legend(frameon=False, fontsize=9)
    fig.suptitle("Clasificador EfficientNetB0 (batch=64) — curva real de entrenamiento", fontsize=11, y=1.03)
    fig.tight_layout()
    fig.savefig(OUT / "curva_clasificador.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_curva_unet():
    df = pd.read_csv(SAL / f"{UNET_ID}_curva.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    ax[0].plot(df.epoca, df.perdida_train, color=NAVY, marker="o", ms=3)
    ax[0].set_title("Pérdida de entrenamiento (BCE + Dice)")
    ax[0].set_xlabel("Época"); ax[0].set_ylabel("Pérdida")
    ax[1].plot(df.epoca, df.val_iou * 100, color=BLUE, marker="o", ms=3, label="IoU")
    ax[1].plot(df.epoca, df.val_dice * 100, color=TEAL, marker="s", ms=3, label="Dice")
    ax[1].axhline(70, color=GRAY, ls="--", lw=1, label="Meta IoU 70 %")
    ax[1].set_title("Validación")
    ax[1].set_xlabel("Época"); ax[1].set_ylabel("%")
    ax[1].legend(frameon=False, fontsize=9)
    fig.suptitle("U-Net ResNet34 (lr=1e-4) — curva real de entrenamiento", fontsize=11, y=1.03)
    fig.tight_layout()
    fig.savefig(OUT / "curva_unet.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_matriz_confusion():
    df = pd.read_csv(SAL / f"{CLF_ID}_por_grupo.csv")
    n = len(CLASES)
    m = np.zeros((n, n), dtype=int)
    for r, p in zip(df.real, df.pred):
        m[r, p] += 1
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    im = ax.imshow(m, cmap="Blues")
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels([ES[c] for c in CLASES], rotation=30, ha="right")
    ax.set_yticklabels([ES[c] for c in CLASES])
    ax.set_xlabel("Predicho"); ax.set_ylabel("Real")
    for i in range(n):
        for j in range(n):
            ax.text(j, i, str(m[i, j]), ha="center", va="center",
                     color="white" if m[i, j] > m.max() / 2 else "black", fontsize=10)
    ax.set_title(f"Matriz de confusión — validación (n={len(df)})", fontsize=10)
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(OUT / "matriz_confusion.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def _recall_medio(celda_json):
    import json
    d = json.loads(celda_json.replace("'", '"'))
    return float(np.mean(list(d.values())))


def fig_hu08_comparacion():
    exp = pd.read_csv(S2 / "experimentos.csv")
    hu08 = exp[(exp.historia == "HU08") & (exp.semilla == 42)]

    clf = hu08[hu08.tarea == "clasificacion"].copy()
    clf["recall_medio"] = clf.val_recall_por_clase.apply(_recall_medio)
    base_clf = 0.9952  # modelo base HU06, semilla 42 (ver experimentos.csv)
    clf["etiqueta"] = clf.apply(lambda r: ("lr=1e-4" if r.lr == 0.0001 else
                                            ("batch=64\n(elegida)" if r.batch == 64 else
                                             ("Sin aumento\n(ablación)" if not r.aumento else "?"))), axis=1)
    filas_clf = [("Base\n(lr=3e-4, batch=32)", base_clf)] + list(zip(clf.etiqueta, clf.recall_medio))

    unet = hu08[hu08.tarea == "segmentacion"].copy()
    base_unet = 0.7970  # modelo base HU07, semilla 42 (ver experimentos.csv)
    unet["etiqueta"] = unet.apply(lambda r: ("lr=1e-4\n(elegida)" if r.lr == 0.0001 else
                                              ("batch=16" if r.batch == 16 else
                                               ("Sin aumento\n(ablación)" if not r.aumento else "?"))), axis=1)
    filas_unet = [("Base\n(lr=3e-4, batch=8)", base_unet)] + list(zip(unet.etiqueta, unet.val_iou))

    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    etq, val = zip(*filas_clf)
    colores = [NAVY if "elegida" in e else GRAY for e in etq]
    ax[0].bar(etq, [v * 100 for v in val], color=colores)
    ax[0].set_ylim(99, 100)
    ax[0].set_title("Clasificador — recall medio de validación por configuración (HU08)")
    ax[0].set_ylabel("%")
    for i, v in enumerate(val):
        ax[0].text(i, v * 100 + 0.01, f"{v * 100:.2f}", ha="center", fontsize=9)

    etq2, val2 = zip(*filas_unet)
    colores2 = [NAVY if "elegida" in e else GRAY for e in etq2]
    ax[1].bar(etq2, [v * 100 for v in val2], color=colores2)
    ax[1].set_ylim(78, 81)
    ax[1].set_title("U-Net — IoU de validación por configuración (HU08)")
    ax[1].set_ylabel("%")
    for i, v in enumerate(val2):
        ax[1].text(i, v * 100 + 0.02, f"{v * 100:.2f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "hu08_comparacion.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_r09_desglose():
    clf = pd.read_csv(SAL / f"{CLF_ID}_por_grupo.csv")
    unet = pd.read_csv(SAL / f"{UNET_ID}_por_grupo.csv")
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    g = clf.groupby("modo").correcto.mean() * 100
    ax[0].bar(g.index, g.values, color=[TEAL, BLUE])
    ax[0].set_ylim(95, 100)
    ax[0].set_title("Clasificador: accuracy por tipo de archivo de origen")
    ax[0].set_ylabel("%")
    for i, (k, v) in enumerate(g.items()):
        ax[0].text(i, v + 0.1, f"{v:.2f}", ha="center", fontsize=9)
    g2 = unet.groupby("modo").iou.mean() * 100
    ax[1].bar(g2.index, g2.values, color=[TEAL, BLUE])
    ax[1].set_ylim(60, 90)
    ax[1].set_title("U-Net: IoU por tipo de archivo de origen (riesgo R09)")
    ax[1].set_ylabel("%")
    for i, (k, v) in enumerate(g2.items()):
        ax[1].text(i, v + 0.5, f"{v:.1f}", ha="center", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "r09_desglose.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig_curva_clasificador()
    fig_curva_unet()
    fig_matriz_confusion()
    fig_hu08_comparacion()
    fig_r09_desglose()
    print("Listo:", OUT)
