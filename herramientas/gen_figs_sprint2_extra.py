# -*- coding: utf-8 -*-
"""Graficos ADICIONALES del informe del Sprint 2, a partir de datos reales (no inventados):
experimentos.csv, salida_sprint2/*_curva.csv, salida_sprint2/*_por_grupo.csv, la salida real de
verificar_preparado.py y el dataset preparado en disco. Mismo estilo que gen_figs_sprint2.py
(paleta NAVY/BLUE/TEAL/GREEN/GRAY, DejaVu Sans, fondo blanco, dpi=150), pero este archivo es
independiente: no modifica ni depende de gen_figs_sprint2.py.

Uso:
    "<raiz del proyecto>/.venv/Scripts/python.exe" herramientas/gen_figs_sprint2_extra.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path as _P

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

_AQUI = _P(__file__).resolve().parent
_RAIZ = _AQUI.parent
S2 = _RAIZ / "03. Implementacion" / "Sprint 2 - Entrenamiento"
SAL = S2 / "salida_sprint2"
S1 = _RAIZ / "03. Implementacion" / "Sprint 1 - Notebooks"
OUT = _AQUI / "figs_sprint2"
OUT.mkdir(exist_ok=True)

NAVY, BLUE, TEAL, GREEN, GRAY = "#1F3864", "#5B84B1", "#2B7A8B", "#8FB89A", "#9AA5B1"
PALETA = [NAVY, BLUE, TEAL, GREEN, GRAY]
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                      "font.family": "DejaVu Sans", "axes.prop_cycle": plt.cycler(color=PALETA)})

CLASES = ["glioma", "meningioma", "pituitary", "no_tumor"]
ES = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Hipófisis", "no_tumor": "Sin tumor"}
PLANO_ES = {"ax": "Axial", "co": "Coronal", "sa": "Sagital"}

UNET_ID = "unet_resnet34_20261023_002334"  # checkpoint HU08 lr=1e-4, semilla 42 (ver experimentos.csv)


def _log_fallo(nombre, exc):
    print(f"[FALLA] {nombre}: {exc}", file=sys.stderr)


def fig_iou_por_clase():
    """Fuente: salida_sprint2/{UNET_ID}_por_grupo.csv (columnas iou, dice, clase)."""
    df = pd.read_csv(SAL / f"{UNET_ID}_por_grupo.csv")
    g = df.groupby("clase")[["iou", "dice"]].mean().reindex(["glioma", "meningioma", "pituitary"])
    etiquetas = [ES[c] for c in g.index]
    x = np.arange(len(g))
    ancho = 0.35
    fig, ax = plt.subplots(figsize=(6.4, 4))
    ax.bar(x - ancho / 2, g.iou * 100, ancho, color=NAVY, label="IoU")
    ax.bar(x + ancho / 2, g.dice * 100, ancho, color=TEAL, label="Dice")
    for i, (iou, dice) in enumerate(zip(g.iou, g.dice)):
        ax.text(i - ancho / 2, iou * 100 + 1, f"{iou * 100:.1f}", ha="center", fontsize=9)
        ax.text(i + ancho / 2, dice * 100 + 1, f"{dice * 100:.1f}", ha="center", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas)
    ax.set_ylabel("%")
    ax.set_ylim(0, 100)
    ax.set_title("U-Net ResNet34 — IoU y Dice de validación por clase de tumor", fontsize=11)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "iou_por_clase.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_iou_por_plano():
    """Fuente: salida_sprint2/{UNET_ID}_por_grupo.csv (columnas iou, plano)."""
    df = pd.read_csv(SAL / f"{UNET_ID}_por_grupo.csv")
    g = df.groupby("plano")["iou"].mean().reindex(["ax", "co", "sa"])
    n = df.groupby("plano")["iou"].count().reindex(["ax", "co", "sa"])
    etiquetas = [f"{PLANO_ES[p]}\n(n={n[p]})" for p in g.index]
    fig, ax = plt.subplots(figsize=(5.6, 4))
    ax.bar(etiquetas, g.values * 100, color=[NAVY, BLUE, TEAL])
    for i, v in enumerate(g.values):
        ax.text(i, v * 100 + 1, f"{v * 100:.1f}", ha="center", fontsize=9)
    ax.set_ylabel("IoU medio (%)")
    ax.set_ylim(0, 100)
    ax.set_title("U-Net ResNet34 — IoU de validación por plano de corte", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "iou_por_plano.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_recall_por_clase_arquitecturas():
    """Fuente: experimentos.csv, filas historia=HU06 (columna val_recall_por_clase, JSON)."""
    exp = pd.read_csv(S2 / "experimentos.csv")
    hu06 = exp[exp.historia == "HU06"].copy()
    hu06["recall"] = hu06.val_recall_por_clase.apply(json.loads)

    arquitecturas = {"efficientnet_b0": "EfficientNetB0", "resnet50": "ResNet50"}
    filas = hu06[hu06.arquitectura.isin(arquitecturas)]

    x = np.arange(len(CLASES))
    ancho = 0.35
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    colores = {"efficientnet_b0": NAVY, "resnet50": BLUE}
    for i, (_, fila) in enumerate(filas.iterrows()):
        vals = [fila.recall[c] * 100 for c in CLASES]
        offset = (i - (len(filas) - 1) / 2) * ancho
        barras = ax.bar(x + offset, vals, ancho, color=colores.get(fila.arquitectura, GRAY),
                         label=arquitecturas.get(fila.arquitectura, fila.arquitectura))
        for b, v in zip(barras, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.1f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([ES[c] for c in CLASES])
    ax.set_ylabel("Recall de validación (%)")
    ax.set_ylim(95, 101)
    ax.set_title("Recall por clase de tumor — EfficientNetB0 vs ResNet50 (HU06)", fontsize=11)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "recall_por_clase_arquitecturas.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_tiempo_entrenamiento():
    """Fuente: experimentos.csv, columnas id, tarea, tiempo_min (las 13 filas)."""
    exp = pd.read_csv(S2 / "experimentos.csv").copy()
    exp["sufijo"] = exp.id.str.rsplit("_", n=1).str[0].str.rsplit("_", n=1).str[-1]
    # sufijo = fecha_hora, p.ej. "20261023_002839" -> usamos la parte de hora HHMMSS como etiqueta corta
    exp["hora"] = exp.id.str.extract(r"_(\d{8}_\d{6})$")[0]
    exp = exp.sort_values("hora").reset_index(drop=True)
    colores = {"clasificacion": NAVY, "segmentacion": TEAL}
    etiquetas = [f"{r.arquitectura}\n{r.hora[-6:]}" for r in exp.itertuples()]
    y = np.arange(len(exp))
    fig, ax = plt.subplots(figsize=(8, 6))
    barras = ax.barh(y, exp.tiempo_min, color=[colores[t] for t in exp.tarea])
    ax.set_yticks(y)
    ax.set_yticklabels(etiquetas, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("Tiempo de entrenamiento (minutos)")
    ax.set_title("Tiempo de entrenamiento de los 13 experimentos del Sprint 2", fontsize=11)
    for b, v in zip(barras, exp.tiempo_min):
        ax.text(v + 0.2, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center", fontsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=colores["clasificacion"]),
               plt.Rectangle((0, 0), 1, 1, color=colores["segmentacion"])]
    ax.legend(handles, ["Clasificación", "Segmentación"], frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "tiempo_entrenamiento.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_curvas_unet_hu08():
    """Fuente: experimentos.csv (filas historia HU07/HU08, tarea=segmentacion, semilla=42) y,
    para cada id, salida_sprint2/<id>_curva.csv (columnas epoca, val_iou)."""
    exp = pd.read_csv(S2 / "experimentos.csv")
    sub = exp[(exp.historia.isin(["HU07", "HU08"])) & (exp.tarea == "segmentacion") & (exp.semilla == 42)]

    def etiqueta(r):
        if r.historia == "HU07":
            return "Base (lr=3e-4, batch=8)"
        if r.lr == 0.0001:
            return "lr=1e-4"
        if not r.aumento:
            return "Sin aumento"
        if r.batch == 16:
            return "Batch=16"
        return r.id

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for color, (_, r) in zip(PALETA, sub.iterrows()):
        curva = pd.read_csv(SAL / f"{r.id}_curva.csv")
        ax.plot(curva.epoca, curva.val_iou * 100, color=color, marker="o", ms=3, label=etiqueta(r))
    ax.set_xlabel("Época")
    ax.set_ylabel("IoU de validación (%)")
    ax.set_title("U-Net ResNet34 (semilla=42) — IoU de validación por época, 4 configuraciones (HU08)",
                 fontsize=10.5)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "curvas_unet_hu08.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig_terminal_verificacion():
    """Fuente: salida real (stdout) de ejecutar ahora, con el interprete del proyecto:
    cd "03. Implementacion/Sprint 1 - Notebooks" && python verificar_preparado.py
    Se captura el texto tal cual (sin reescribir ni resumir) y se renderiza como imagen de
    terminal."""
    python_exe = _RAIZ / ".venv" / "Scripts" / "python.exe"
    resultado = subprocess.run(
        [str(python_exe), "verificar_preparado.py"],
        cwd=str(S1), capture_output=True, text=True, timeout=600,
    )
    salida = resultado.stdout
    if resultado.returncode not in (0, 1):
        # 0 = todo correcto, 1 = alguna comprobacion fallo (igual es texto real); otro codigo = error real
        raise RuntimeError(f"verificar_preparado.py devolvio codigo {resultado.returncode}: {resultado.stderr}")
    lineas = salida.rstrip("\n").split("\n")

    alto = 0.42 + 0.30 * len(lineas)
    fig, ax = plt.subplots(figsize=(9.5, alto))
    fig.patch.set_facecolor("#1E1E1E")
    ax.set_facecolor("#1E1E1E")
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    titulo = 'python verificar_preparado.py'
    y0 = 1.0
    paso = 1.0 / (len(lineas) + 1.6)
    ax.text(0.012, y0 - paso * 0.5, f"$ {titulo}", color="#7FDBCA", fontsize=10.5,
            family="monospace", va="top", ha="left")
    for i, linea in enumerate(lineas):
        color = "#D4D4D4"
        if linea.strip().startswith("OK"):
            color = "#8FB89A"
        elif "FALLA" in linea or "RESULTADO:" in linea and "todo correcto" not in linea:
            color = "#D18A8A"
        elif linea.strip().startswith(("1.", "2.", "3.", "4.")):
            color = "#5B84B1"
        elif "RESULTADO: todo correcto" in linea:
            color = "#8FB89A"
        ax.text(0.012, y0 - paso * (i + 1.6), linea if linea.strip() else " ", color=color,
                fontsize=10, family="monospace", va="top", ha="left")
    fig.savefig(OUT / "terminal_verificacion.png", dpi=150, facecolor=fig.get_facecolor(),
                bbox_inches="tight")
    plt.close(fig)


def fig_muestra_dataset():
    """Fuente: imagenes reales ya preparadas en <carpeta de usuario>/datasets/brisc2025_preparado/
    imagenes/train/<clase>/*.png (misma raiz que datos.py::raiz_preparado())."""
    raiz = _P(os.environ.get("BRISC_PREPARADO", _P.home() / "datasets" / "brisc2025_preparado"))
    fig, axes = plt.subplots(2, 4, figsize=(10, 5.2))
    for col, clase in enumerate(CLASES):
        carpeta = raiz / "imagenes" / "train" / clase
        archivos = sorted(carpeta.glob("*.png"))[:2]
        if len(archivos) < 2:
            raise RuntimeError(f"No hay suficientes imagenes en {carpeta}")
        for fila, archivo in enumerate(archivos):
            with Image.open(archivo) as im:
                arr = np.asarray(im.convert("L"))
            ax = axes[fila, col]
            ax.imshow(arr, cmap="gray")
            ax.axis("off")
            if fila == 0:
                ax.set_title(ES[clase], fontsize=11)
    fig.suptitle("Muestra real del dataset preparado (2 imágenes por clase, partición train)",
                 fontsize=11, y=0.99)
    fig.tight_layout()
    fig.savefig(OUT / "muestra_dataset.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


FIGURAS = [
    ("iou_por_clase.png", fig_iou_por_clase),
    ("iou_por_plano.png", fig_iou_por_plano),
    ("recall_por_clase_arquitecturas.png", fig_recall_por_clase_arquitecturas),
    ("tiempo_entrenamiento.png", fig_tiempo_entrenamiento),
    ("curvas_unet_hu08.png", fig_curvas_unet_hu08),
    ("terminal_verificacion.png", fig_terminal_verificacion),
    ("muestra_dataset.png", fig_muestra_dataset),
]


if __name__ == "__main__":
    ok, fallidas = [], []
    for nombre, fn in FIGURAS:
        try:
            fn()
            ok.append(nombre)
            print(f"[OK] {nombre}")
        except Exception as exc:  # noqa: BLE001 - seguimos con las demas figuras
            fallidas.append((nombre, str(exc)))
            _log_fallo(nombre, exc)
    print("\nListo:", OUT)
    print("Generadas:", ", ".join(ok) if ok else "(ninguna)")
    if fallidas:
        print("Fallidas:", ", ".join(n for n, _ in fallidas))
