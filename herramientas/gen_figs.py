# -*- coding: utf-8 -*-
"""Graficos para el informe y la presentacion del Sprint 1 (datos reales y modelo con supuestos)."""
from pathlib import Path as _P
_AQUI = _P(__file__).resolve().parent
_RAIZ = _AQUI.parent
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROY = _RAIZ
SAL = PROY / "03. Implementacion/Sprint 1 - Notebooks/salida_sprint1"
OUT = _AQUI / "figs"
OUT.mkdir(exist_ok=True)

# paleta sobria: azul marino, azul acero, verde azulado y grises (sin naranja)
NAVY, BLUE, ORANGE, TEAL, GRAY = "#1F3864", "#1F3864", "#2B7A8B", "#5B84B1", "#7F7F7F"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
ES = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Tumor de hipófisis", "no_tumor": "Sin tumor"}

# ---------------------------------------------------------------- 1. sector privado
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
nombres = ["Público", "EsSalud", "Privado"]
vals = [8866, 381, 9820]
pct = ["46 %", "2 %", "52 %"]
b = ax[0].barh(nombres, vals, color=[BLUE, TEAL, ORANGE])
for r, v, p in zip(b, vals, pct):
    ax[0].text(v + 150, r.get_y() + r.get_height() / 2, f"{v:,}".replace(",", ".") + f"  ({p})", va="center", fontsize=9)
ax[0].set_xlim(0, 13500)
ax[0].set_title("Establecimientos de salud categorizados\n(19.067, mayo de 2022)", fontsize=10)
ax[0].invert_yaxis()
ax[0].set_xticks([])
ax[0].spines["bottom"].set_visible(False)
nombres = ["SIS", "EsSalud", "Seguro privado\n(sin EPS)"]
vals = [69.1, 28.5, 6.7]
b = ax[1].barh(nombres, vals, color=[BLUE, TEAL, ORANGE])
for r, v in zip(b, vals):
    ax[1].text(v + 1.2, r.get_y() + r.get_height() / 2, f"{v:.1f} %".replace(".", ","), va="center", fontsize=9)
ax[1].set_xlim(0, 85)
ax[1].set_title("Población según seguro (2022)\n(una persona puede tener más de uno)", fontsize=10)
ax[1].invert_yaxis()
ax[1].set_xticks([])
ax[1].spines["bottom"].set_visible(False)
fig.text(0.5, 0.005, "Fuente: SuSalud y Minsa, citados por Videnza Consultores para ComexPerú (agosto de 2022)", ha="center", fontsize=8, color=GRAY)
plt.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT / "sector_privado.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- 2. escenario de clinica
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
tam = ["Pequeña\n(1 equipo)", "Mediana\n(2 equipos)", "Grande\n(4 equipos)"]
anio = [1200, 3600, 9000]
b = ax[0].bar(tam, anio, color=BLUE)
for r, v in zip(b, anio):
    ax[0].text(r.get_x() + r.get_width() / 2, v + 150, f"{v:,}".replace(",", "."), ha="center", fontsize=9)
ax[0].set_title("Resonancias cerebrales al año (supuesto)", fontsize=10)
ax[0].set_ylim(0, 10500)
lo = np.array([33, 100, 250]); hi = np.array([50, 150, 375])
x = np.arange(3)
ax[1].bar(x, hi, color="#9DB4DB", label="con 30 min por estudio")
ax[1].bar(x, lo, color=NAVY, label="con 20 min por estudio")
for xi, l, h in zip(x, lo, hi):
    ax[1].text(xi, h + 8, f"{l} a {h} h", ha="center", fontsize=9)
ax[1].set_xticks(x)
ax[1].set_xticklabels(tam)
ax[1].set_title("Horas médicas de lectura cerebral al mes", fontsize=10)
ax[1].set_ylim(0, 440)
ax[1].legend(fontsize=8, frameon=False, loc="upper left")
fig.text(0.5, 0.005, "Modelo con supuestos del equipo (25 % de las resonancias son de cerebro): no son datos de ninguna clínica", ha="center", fontsize=8, color=GRAY)
plt.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT / "escenario_clinica.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- 3. prevalencia y valor predictivo
def ppv(p, se=0.95, sp=0.95):
    return se * p / (se * p + (1 - sp) * (1 - p))

p = np.linspace(0.005, 0.9, 300)
fig, ax = plt.subplots(figsize=(7.4, 4.2))
ax.plot(p * 100, ppv(p) * 100, color=BLUE, lw=2.5)
for px, lab, col, dx, dy in [(0.03, "Clínica (supuesto 3 %)", ORANGE, 4, -2), (0.80, "BRISC (80 % con tumor)", TEAL, -34, -14)]:
    y = ppv(px) * 100
    ax.scatter([px * 100], [y], s=70, color=col, zorder=3)
    ax.annotate(f"{lab}\n{y:.0f} % de los señalados tienen tumor", (px * 100, y), xytext=(px * 100 + dx, y + dy), fontsize=9, color=col)
ax.set_xlabel("Prevalencia de tumor entre los estudios (%)")
ax.set_ylabel("De los señalados como tumor,\nlos que realmente lo tienen (%)")
ax.set_ylim(0, 105)
ax.set_xlim(0, 92)
ax.set_title("Mismo modelo, distinta prevalencia (sensibilidad 95 %, especificidad 95 %: valores hipotéticos)", fontsize=9)
ax.grid(alpha=0.25)
plt.tight_layout()
fig.savefig(OUT / "prevalencia_ppv.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- 4. modo de archivo por clase
img = pd.read_csv(SAL / "perfil_datos/perfil_imagenes.csv")
orden = ["glioma", "meningioma", "pituitary", "no_tumor"]
g = img.groupby(["cls", "mode"]).size().unstack(fill_value=0).reindex(orden)
tot = g.sum(axis=1)
fig, ax = plt.subplots(figsize=(7.4, 3.6))
y = np.arange(len(orden))
gris = g["L"] / tot * 100
rgb = g["RGB"] / tot * 100
ax.barh(y, gris, color=BLUE, label="Escala de grises (1 canal)")
ax.barh(y, rgb, left=gris, color=ORANGE, label="RGB (3 canales iguales)")
for i, (a, b_) in enumerate(zip(gris, rgb)):
    if a > 6:
        ax.text(a / 2, i, f"{a:.0f} %", ha="center", va="center", color="white", fontsize=9)
    if b_ > 6:
        ax.text(a + b_ / 2, i, f"{b_:.0f} %", ha="center", va="center", color="white", fontsize=9)
ax.set_yticks(y)
ax.set_yticklabels([ES[c] for c in orden])
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel("% de las imágenes de la clase")
ax.set_title("Modo de archivo de las imágenes por clase", fontsize=10)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2, frameon=False, fontsize=9)
plt.tight_layout()
fig.savefig(OUT / "modo_por_clase.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- 5. entrenamiento vs prueba
ks = pd.read_csv(SAL / "perfil_datos/comparacion_train_test.csv")
nombre = {"intensidad media del cerebro": "Brillo del cerebro", "fraccion de cerebro": "Fracción de cerebro", "tamano de archivo": "Tamaño de archivo",
          "area del tumor (fraccion)": "Tamaño del tumor", "contraste del tumor": "Contraste del tumor"}
ks["etq"] = ks.variable.map(nombre) + " · " + ks.clase.map(lambda c: ES.get(c, c))
ks = ks.sort_values("ks")
fig, ax = plt.subplots(1, 2, figsize=(10, 4.4), gridspec_kw={"width_ratios": [1, 2.2]})
modo = img.groupby("split")["mode"].apply(lambda s: (s == "L").mean() * 100)
b = ax[0].bar(["Entrenamiento", "Prueba"], [modo["train"], modo["test"]], color=[BLUE, ORANGE])
for r, v in zip(b, [modo["train"], modo["test"]]):
    ax[0].text(r.get_x() + r.get_width() / 2, v + 1, f"{v:.1f} %".replace(".", ","), ha="center", fontsize=9)
ax[0].set_ylim(0, 75)
ax[0].set_title("Imágenes en escala de grises", fontsize=10)
col = [ORANGE if p < 0.001 else "#B7B7B7" for p in ks.p]
ax[1].barh(ks.etq, ks.ks, color=col)
ax[1].set_title("Cuánto difiere cada medida entre entrenamiento y prueba\n(KS: 0 = iguales, 1 = totalmente distintas)", fontsize=10)
ax[1].set_xlim(0, 0.35)
ax[1].tick_params(axis="y", labelsize=7.5)
from matplotlib.patches import Patch
ax[1].legend(handles=[Patch(color=ORANGE, label="diferencia significativa (p < 0,001)"), Patch(color="#B7B7B7", label="sin diferencia clara")], fontsize=8, frameon=False, loc="lower right")
plt.tight_layout()
fig.savefig(OUT / "train_vs_test.png", dpi=150)
plt.close(fig)

# ---------------------------------------------------------------- 6. particion
part = pd.read_csv(SAL / "particion/particion_completa.csv")
t = pd.crosstab(part.cls, part.particion).reindex(orden)[["train", "val", "test"]]
fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
x = np.arange(len(orden)); w = 0.26
for k, (c, col, lab) in enumerate([("train", BLUE, "Entrenamiento"), ("val", TEAL, "Validación"), ("test", ORANGE, "Prueba oficial")]):
    bb = ax[0].bar(x + (k - 1) * w, t[c], w, color=col, label=lab)
    for r, v in zip(bb, t[c]):
        ax[0].text(r.get_x() + r.get_width() / 2, v + 15, f"{v:,}".replace(",", "."), ha="center", fontsize=7)
ax[0].set_xticks(x)
ax[0].set_xticklabels([ES[c].replace("Tumor de ", "T. de ") for c in orden], fontsize=8)
ax[0].set_title("Imágenes por clase y partición", fontsize=10)
ax[0].legend(fontsize=8, frameon=False)
tp = pd.crosstab(part.plane, part.particion)[["train", "val", "test"]]
tp.index = ["Axial", "Coronal", "Sagital"] if list(tp.index) == ["ax", "co", "sa"] else tp.index
tp = tp / tp.sum(axis=0) * 100
bottom = np.zeros(3)
for pl, col in zip(tp.index, [BLUE, ORANGE, TEAL]):
    ax[1].bar(["Entrenamiento", "Validación", "Prueba"], tp.loc[pl].values, bottom=bottom, color=col, label=pl)
    for i, v in enumerate(tp.loc[pl].values):
        ax[1].text(i, bottom[i] + v / 2, f"{v:.0f} %", ha="center", va="center", color="white", fontsize=8)
    bottom += tp.loc[pl].values
ax[1].set_title("Planos de corte en cada partición", fontsize=10)
ax[1].legend(fontsize=8, frameon=False, bbox_to_anchor=(1.0, 1.0))
plt.tight_layout()
fig.savefig(OUT / "particion.png", dpi=150)
plt.close(fig)
print("ok", sorted(p.name for p in OUT.iterdir()))
