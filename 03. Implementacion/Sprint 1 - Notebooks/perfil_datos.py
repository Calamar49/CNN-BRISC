"""Perfil detallado de los datos de BRISC 2025 (HU02: comprension de los datos).

Complementa el notebook 01_HU02_EDA_BRISC.ipynb con medidas sobre el contenido de las imagenes y las mascaras:
formato y canales, intensidad, fraccion de cerebro, contraste del tumor, localizacion y numero de lesiones por mascara,
y una comparacion entre entrenamiento y prueba oficial.

Uso:
    python perfil_datos.py

Resultados en salida_sprint1/perfil_datos/ (CSV por imagen y por mascara, resumen_perfil.json y figuras).
"""
import json
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy import ndimage
from scipy.stats import ks_2samp

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parents[1]
OUT = AQUI / "salida_sprint1" / "perfil_datos"
BG_THR = 10          # pixel de fondo (negro) si su valor <= 10 sobre 255
MASK_THR = 127       # igual que en los notebooks
MAP = 64             # resolucion del mapa de localizacion

PALETA = ["#1F3864", "#5B84B1", "#2B7A8B", "#8FB89A", "#9AA5B1"]
plt.rcParams["axes.prop_cycle"] = plt.cycler(color=PALETA)
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False

CLASES = ["glioma", "meningioma", "pituitary", "no_tumor"]
ES = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Tumor de hipófisis", "no_tumor": "Sin tumor"}


def raiz():
    manual = os.environ.get("BRISC_ROOT")
    for b in ([Path(manual)] if manual else []) + [Path.home() / "datasets", PROYECTO / "data"]:
        for dp, dn, fn in os.walk(b):
            if "manifest.csv" in fn:
                return Path(dp)
    raise SystemExit("No encuentro el dataset. Ejecuta primero: python descargar_brisc.py")


def cuadrar(a):
    """rellena con ceros a cuadrado (igual que el cargador del Sprint 1)"""
    h, w = a.shape[:2]
    if h == w:
        return a
    s = max(h, w)
    out = np.zeros((s, s) + a.shape[2:], dtype=a.dtype)
    y0, x0 = (s - h) // 2, (s - w) // 2
    out[y0:y0 + h, x0:x0 + w] = a
    return out


def main():
    root = raiz()
    OUT.mkdir(parents=True, exist_ok=True)
    man = pd.read_csv(root / "manifest.csv")
    cls = man[(man.task == "classification") & (~man.is_mask)].copy()
    cls["path"] = cls.relative_path.str.replace("\\", "/", regex=False)
    seg = man[(man.task == "segmentation") & (man.is_mask)].copy()
    seg["path"] = seg.relative_path.str.replace("\\", "/", regex=False)
    seg["img_path"] = seg.linked_image.str.replace("\\", "/", regex=False)
    seg_by_name = {r.filename.rsplit(".", 1)[0]: r for r in seg.itertuples()}

    # ---------------------------------------------------------------- imagenes (clasificacion)
    rows = []
    gris_igual = 0
    for i, r in enumerate(cls.itertuples()):
        with Image.open(root / r.path) as im:
            modo, fmt, size = im.mode, im.format, im.size
            arr = np.asarray(im)
        if arr.ndim == 3:
            if arr.shape[2] == 3 and np.abs(arr[..., 0].astype(int) - arr[..., 1]).max() <= 2 and np.abs(arr[..., 1].astype(int) - arr[..., 2]).max() <= 2:
                gris_igual += 1
            g = arr[..., :3].mean(axis=2)
        else:
            g = arr.astype(float)
        cerebro = g > BG_THR
        rows.append(dict(filename=r.filename, split=r.split, cls=r.tumor_label, plane=r.plane_label, mode=modo, fmt=fmt,
                         width=size[0], height=size[1], bytes=r.file_size_bytes, mean_all=g.mean(), std_all=g.std(),
                         brain_frac=cerebro.mean(), mean_brain=g[cerebro].mean() if cerebro.any() else 0.0,
                         p99=float(np.percentile(g, 99)), tiene_mascara=r.filename.rsplit(".", 1)[0] in seg_by_name))
        if (i + 1) % 1000 == 0:
            print(f"  imagenes {i + 1}/{len(cls)}", flush=True)
    img = pd.DataFrame(rows)
    img.to_csv(OUT / "perfil_imagenes.csv", index=False)

    # ---------------------------------------------------------------- mascaras (segmentacion)
    mrows = []
    maps = {c: np.zeros((MAP, MAP), dtype=np.float64) for c in CLASES[:3]}
    cuenta = {c: 0 for c in CLASES[:3]}
    for i, r in enumerate(seg.itertuples()):
        m = np.asarray(Image.open(root / r.path).convert("L")) > MASK_THR
        with Image.open(root / r.img_path) as im:
            g = np.asarray(im.convert("L"), dtype=float)
        h, w = m.shape
        lab, ncomp = ndimage.label(m)
        sizes = ndimage.sum(m, lab, range(1, ncomp + 1)) if ncomp else np.array([])
        ys, xs = np.nonzero(m)
        cy, cx = (ys.mean() / h, xs.mean() / w) if len(ys) else (np.nan, np.nan)
        cerebro = g > BG_THR
        dentro = g[m].mean() if m.any() else np.nan
        fuera = g[cerebro & ~m].mean() if (cerebro & ~m).any() else np.nan
        toca_borde = bool(m[0, :].any() or m[-1, :].any() or m[:, 0].any() or m[:, -1].any())
        mrows.append(dict(filename=r.filename, split=r.split, cls=r.tumor_label, plane=r.plane_label, h=h, w=w,
                          area_px=int(m.sum()), area_frac=float(m.mean()), ncomp=int(ncomp),
                          comp_mayor_frac=float(sizes.max() / m.sum()) if ncomp else np.nan,
                          cy=cy, cx=cx, toca_borde=toca_borde, int_tumor=dentro, int_resto=fuera,
                          contraste=dentro / fuera if fuera and fuera > 0 else np.nan,
                          area_en_cerebro=float(m.sum() / cerebro.sum()) if cerebro.any() else np.nan))
        sq = cuadrar(m.astype(np.float32))
        small = np.asarray(Image.fromarray(sq).resize((MAP, MAP), Image.BILINEAR), dtype=np.float64)
        maps[r.tumor_label] += small
        cuenta[r.tumor_label] += 1
        if (i + 1) % 1000 == 0:
            print(f"  mascaras {i + 1}/{len(seg)}", flush=True)
    msk = pd.DataFrame(mrows)
    msk.to_csv(OUT / "perfil_mascaras.csv", index=False)

    # ---------------------------------------------------------------- resumen
    res = {"imagenes": int(len(img)), "modo_imagen": img["mode"].value_counts().to_dict(), "formato": img.fmt.value_counts().to_dict(),
           "rgb_con_canales_iguales": int(gris_igual), "mascaras": int(len(msk))}
    res["tamano_archivo_bytes_por_clase"] = img.groupby("cls").bytes.describe()[["mean", "50%", "min", "max"]].round(0).to_dict("index")
    res["intensidad_media_por_clase"] = img.groupby("cls").mean_brain.describe()[["mean", "std", "min", "50%", "max"]].round(1).to_dict("index")
    res["fraccion_cerebro_por_clase"] = img.groupby("cls").brain_frac.describe()[["mean", "std", "min", "50%", "max"]].round(3).to_dict("index")
    res["intensidad_media_por_plano"] = img.groupby("plane").mean_brain.describe()[["mean", "std"]].round(1).to_dict("index")
    res["relacion_aspecto_no_cuadrada"] = int((img.width != img.height).sum())
    res["tam_modal"] = {f"{w}x{h}": int(n) for (w, h), n in img.groupby(["width", "height"]).size().sort_values(ascending=False).head(5).items()}
    res["componentes_por_mascara"] = msk.ncomp.value_counts().sort_index().to_dict()
    res["mascaras_con_mas_de_un_componente"] = int((msk.ncomp > 1).sum())
    res["mascaras_tocan_borde"] = int(msk.toca_borde.sum())
    res["area_frac_percentiles_por_clase"] = msk.groupby("cls").area_frac.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).round(4).to_dict("index")
    res["contraste_tumor_resto_por_clase"] = msk.groupby("cls").contraste.describe()[["mean", "50%", "min", "max"]].round(2).to_dict("index")
    res["tumor_mas_brillante_que_el_resto_pct"] = float((msk.contraste > 1).mean() * 100)
    res["centroide_por_clase"] = {c: {"cx_media": round(float(g.cx.mean()), 3), "cx_desvio": round(float(g.cx.std()), 3), "cy_media": round(float(g.cy.mean()), 3), "cy_desvio": round(float(g.cy.std()), 3)} for c, g in msk.groupby("cls")}
    res["area_frac_por_plano"] = msk.groupby("plane").area_frac.median().round(4).to_dict()
    res["area_frac_menor_0_2pct"] = int((msk.area_frac < 0.002).sum())
    res["area_frac_mayor_5pct"] = int((msk.area_frac > 0.05).sum())

    # entrenamiento vs prueba (prueba KS de dos muestras)
    ks = []
    for nombre, tabla, col in [("intensidad media del cerebro", img, "mean_brain"), ("fraccion de cerebro", img, "brain_frac"),
                               ("tamano de archivo", img, "bytes"), ("area del tumor (fraccion)", msk, "area_frac"),
                               ("contraste del tumor", msk, "contraste")]:
        for c in sorted(tabla.cls.unique()):
            a = tabla[(tabla.split == "train") & (tabla.cls == c)][col].dropna()
            b = tabla[(tabla.split == "test") & (tabla.cls == c)][col].dropna()
            if len(a) > 5 and len(b) > 5:
                s = ks_2samp(a, b)
                ks.append(dict(variable=nombre, clase=c, n_train=len(a), n_test=len(b), media_train=round(float(a.mean()), 4),
                               media_test=round(float(b.mean()), 4), ks=round(float(s.statistic), 3), p=float(s.pvalue)))
    pd.DataFrame(ks).to_csv(OUT / "comparacion_train_test.csv", index=False)
    res["ks_train_test"] = ks
    (OUT / "resumen_perfil.json").write_text(json.dumps(res, ensure_ascii=False, indent=2, default=float), encoding="utf-8")

    # ---------------------------------------------------------------- figuras
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.6))
    for ax, c in zip(axes, CLASES[:3]):
        mp = maps[c] / max(cuenta[c], 1)
        im_ = ax.imshow(mp, cmap="Blues", vmin=0)
        ax.set_title(f"{ES[c]} (n={cuenta[c]})", fontsize=10)
        ax.axis("off")
        fig.colorbar(im_, ax=ax, fraction=0.046, pad=0.02)
    fig.suptitle("Dónde está el tumor: proporción de máscaras que cubren cada zona (imagen cuadrada)", fontsize=10)
    plt.tight_layout()
    fig.savefig(OUT / "mapa_localizacion_tumor.png", dpi=130)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    datos = [img[img.cls == c].mean_brain for c in CLASES]
    axes[0].boxplot(datos, showfliers=False, medianprops=dict(color="#1F3864", lw=2))
    axes[0].set_xticklabels([ES[c] for c in CLASES])
    axes[0].set_title("Intensidad media del cerebro (0–255)", fontsize=10)
    axes[0].tick_params(axis="x", labelrotation=15)
    datos = [img[img.cls == c].brain_frac for c in CLASES]
    axes[1].boxplot(datos, showfliers=False, medianprops=dict(color="#1F3864", lw=2))
    axes[1].set_xticklabels([ES[c] for c in CLASES])
    axes[1].set_title("Fracción de la imagen ocupada por cerebro", fontsize=10)
    axes[1].tick_params(axis="x", labelrotation=15)
    plt.tight_layout()
    fig.savefig(OUT / "intensidad_y_cerebro_por_clase.png", dpi=130)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for c in CLASES[:3]:
        axes[0].hist(msk[msk.cls == c].contraste.dropna().clip(upper=4), bins=40, alpha=0.55, label=ES[c])
    axes[0].axvline(1, color="k", lw=0.8, ls="--")
    axes[0].set_title("Brillo del tumor / brillo del resto del cerebro", fontsize=10)
    axes[0].legend(fontsize=8)
    cc = msk.ncomp.clip(upper=5).value_counts().sort_index()
    axes[1].bar([str(k) if k < 5 else "5 o más" for k in cc.index], cc.values, color="#1F3864")
    axes[1].set_title("Regiones separadas por máscara", fontsize=10)
    axes[1].set_ylabel("máscaras")
    plt.tight_layout()
    fig.savefig(OUT / "contraste_y_regiones.png", dpi=130)
    plt.close(fig)
    print("Listo:", OUT)


if __name__ == "__main__":
    main()
