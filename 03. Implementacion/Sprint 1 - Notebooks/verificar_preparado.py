"""Comprueba que el dataset preparado (preparar_dataset.py) esta completo y es igual a lo que produce el cargador del notebook 02_HU03.

Uso:
    python verificar_preparado.py
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parents[1]
SALIDA = Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))
IMG_SIZE, MASK_THR = 256, 127
fallos = []


def comprobar(ok, texto):
    print(("  OK  " if ok else "  FALLA  ") + texto)
    if not ok:
        fallos.append(texto)


def raiz_dataset():
    manual = os.environ.get("BRISC_ROOT")
    for b in ([Path(manual)] if manual else []) + [Path.home() / "datasets", PROYECTO / "data"]:
        for dp, _dn, fn in os.walk(b):
            if "manifest.csv" in fn and "classification_task" in os.listdir(dp):
                return Path(dp)
    return None


def cuadrar(im, modo):
    w, h = im.size
    if w == h:
        return im
    lado = max(w, h)
    lienzo = Image.new(modo, (lado, lado), 0)
    lienzo.paste(im, ((lado - w) // 2, (lado - h) // 2))
    return lienzo


def main():
    man_path = SALIDA / "manifest_preparado.csv"
    if not man_path.exists():
        print("No encuentro", man_path, "\nEjecuta primero: python preparar_dataset.py")
        return 1
    m = pd.read_csv(man_path)
    root = raiz_dataset()
    print("Carpeta:", SALIDA)

    print("\n1. Conteos")
    c = m.particion.value_counts()
    comprobar(len(m) == 6000, f"6.000 imagenes en el manifest ({len(m)})")
    comprobar((c.get("train"), c.get("val"), c.get("test")) == (3999, 1001, 1000), f"entrenamiento / validacion / prueba = {c.get('train')} / {c.get('val')} / {c.get('test')}")
    comprobar(int(m.tiene_mascara.sum()) == 4793, f"4.793 mascaras ({int(m.tiene_mascara.sum())})")
    comprobar(int(m[m.clase == "no_tumor"].tiene_mascara.sum()) == 0, "ninguna imagen sin tumor tiene mascara")
    comprobar(int(m.duplicado_exacto.sum()) == 96, f"96 archivos marcados como duplicado exacto ({int(m.duplicado_exacto.sum())})")
    en_disco = sum(1 for _ in (SALIDA / "imagenes").rglob("*.png"))
    en_disco_m = sum(1 for _ in (SALIDA / "mascaras").rglob("*.png"))
    comprobar(en_disco == 6000 and en_disco_m == 4793, f"archivos en disco: {en_disco} imagenes y {en_disco_m} mascaras")

    print("\n2. Formato de los archivos")
    malas_img, malas_msk, valores = 0, 0, set()
    for r in m.itertuples():
        with Image.open(SALIDA / r.ruta_imagen) as im:
            if im.size != (IMG_SIZE, IMG_SIZE) or im.mode != "L":
                malas_img += 1
        if r.tiene_mascara:
            a = np.asarray(Image.open(SALIDA / r.ruta_mascara))
            valores |= set(np.unique(a).tolist())
            if a.shape != (IMG_SIZE, IMG_SIZE) or a.max() == 0:
                malas_msk += 1
    comprobar(malas_img == 0, "todas las imagenes son de 256 x 256 en un canal")
    comprobar(malas_msk == 0, "todas las mascaras son de 256 x 256 y no estan vacias")
    comprobar(valores <= {0, 255}, f"las mascaras solo tienen los valores {sorted(valores)}")

    print("\n3. Particion")
    g = m[m.grupo_hash.astype(str) != ""]
    gt = set(g[g.particion == "train"].grupo_hash)
    gv = set(g[g.particion == "val"].grupo_hash)
    comprobar(not (gt & gv), "ningun grupo de imagenes parecidas esta repartido entre entrenamiento y validacion")
    comprobar(set(m[m.particion == "test"].particion_oficial) == {"test"}, "la prueba son exactamente las imagenes de la prueba oficial")
    comprobar(set(m[m.particion != "test"].particion_oficial) == {"train"}, "entrenamiento y validacion salen solo del entrenamiento oficial")
    prop = m[m.particion != "test"].groupby("clase").particion.apply(lambda s: (s == "val").mean())
    comprobar(bool(((prop > 0.19) & (prop < 0.21)).all()), "validacion cercana al 20 % en cada clase: " + ", ".join(f"{k} {v:.3f}" for k, v in prop.items()))

    print("\n4. Igual que el cargador del notebook 02_HU03 (muestra de 150)")
    if root is None:
        print("  (se omite: no encuentro el dataset original)")
    else:
        man = pd.read_csv(root / "manifest.csv")
        orig = man[(man.task == "classification") & (~man.is_mask)].set_index("filename").relative_path.str.replace("\\", "/", regex=False)
        seg = man[(man.task == "segmentation") & (man.is_mask)].set_index("filename").relative_path.str.replace("\\", "/", regex=False)
        muestra = m.sample(150, random_state=42)
        dif_i, dif_m = 0, 0
        for r in muestra.itertuples():
            with Image.open(root / orig[r.archivo + ".jpg"]) as im:
                a = cuadrar(im.convert("RGB"), "RGB").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
            a = np.asarray(a)[..., 0]
            b = np.asarray(Image.open(SALIDA / r.ruta_imagen))
            if not np.array_equal(a, b):
                dif_i += 1
            if r.tiene_mascara:
                with Image.open(root / seg[r.archivo + ".png"]) as mk:
                    a = cuadrar(mk.convert("L"), "L").resize((IMG_SIZE, IMG_SIZE), Image.NEAREST)
                a = (np.asarray(a) > MASK_THR).astype(np.uint8) * 255
                b = np.asarray(Image.open(SALIDA / r.ruta_mascara))
                if not np.array_equal(a, b):
                    dif_m += 1
        comprobar(dif_i == 0, f"imagenes identicas a las del cargador ({150 - dif_i} de 150)")
        comprobar(dif_m == 0, "mascaras identicas a las del cargador")

    print()
    if fallos:
        print(f"RESULTADO: {len(fallos)} comprobacion(es) fallaron")
        return 1
    print("RESULTADO: todo correcto")
    return 0


if __name__ == "__main__":
    sys.exit(main())
