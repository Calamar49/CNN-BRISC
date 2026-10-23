"""Genera el dataset BRISC ya preparado (etapa 3 del Sprint 1) en una carpeta lista para entrenar.

Aplica a cada imagen lo mismo que hace el cargador del notebook 02_HU03:
  - imagen en un solo canal (en BRISC las imagenes RGB tienen los 3 canales iguales),
  - relleno con ceros hasta un cuadrado, centrando la imagen (sin deformarla),
  - redimension a 256 x 256 (interpolacion bilineal),
  - mascara binarizada con umbral > 127 (0 = fondo, 255 = tumor) y redimension con "nearest",
  - reparto en entrenamiento / validacion / prueba segun salida_sprint1/particion/particion_completa.csv.

No modifica el dataset original ni elimina ningun archivo. La normalizacion (media y desvio de ImageNet) no se guarda
en los archivos: se aplica al cargar.

Uso:
    python preparar_dataset.py

Antes hay que haber ejecutado:  python descargar_brisc.py  y  python ejecutar_sprint1.py
Carpeta de salida: ~/datasets/brisc2025_preparado  (cambiala con la variable de entorno BRISC_PREPARADO)
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parents[1]
PARTICION = AQUI / "salida_sprint1" / "particion" / "particion_completa.csv"
SALIDA = Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))
IMG_SIZE = 256
MASK_THR = 127


def raiz_dataset():
    manual = os.environ.get("BRISC_ROOT")
    for b in ([Path(manual)] if manual else []) + [Path.home() / "datasets", PROYECTO / "data"]:
        for dp, _dn, fn in os.walk(b):
            if "manifest.csv" in fn and "classification_task" in os.listdir(dp):
                return Path(dp)
    return None


def cuadrar(im, modo):
    """rellena con ceros hasta un cuadrado, centrando la imagen"""
    w, h = im.size
    if w == h:
        return im
    lado = max(w, h)
    lienzo = Image.new(modo, (lado, lado), 0)
    lienzo.paste(im, ((lado - w) // 2, (lado - h) // 2))
    return lienzo


def main():
    root = raiz_dataset()
    if root is None:
        print("No encuentro el dataset. Ejecuta primero: python descargar_brisc.py")
        return 1
    if not PARTICION.exists():
        print("No encuentro", PARTICION, "\nEjecuta primero: python ejecutar_sprint1.py")
        return 1
    part = pd.read_csv(PARTICION)
    man = pd.read_csv(root / "manifest.csv")
    cls_man = man[(man.task == "classification") & (~man.is_mask)].copy()
    cls_man["file"] = cls_man.filename
    sha = cls_man.set_index("file")["sha256"]
    repetido = cls_man.sha256.duplicated(keep=False)
    dup = cls_man.set_index("file")[repetido.values].index
    ancho = cls_man.set_index("file")["width"]
    alto = cls_man.set_index("file")["height"]

    print(f"Dataset original: {root}\nSalida: {SALIDA}\nImagenes a procesar: {len(part)}")
    filas = []
    for i, r in enumerate(part.itertuples(), 1):
        split, clase = r.particion, r.cls
        nombre = Path(r.file).stem
        (SALIDA / "imagenes" / split / clase).mkdir(parents=True, exist_ok=True)
        with Image.open(root / r.path) as im:
            g = im.convert("L")
        g = cuadrar(g, "L").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
        ruta_img = f"imagenes/{split}/{clase}/{nombre}.png"
        g.save(SALIDA / ruta_img)

        ruta_msk, area = "", np.nan
        if isinstance(r.mask, str):
            (SALIDA / "mascaras" / split / clase).mkdir(parents=True, exist_ok=True)
            with Image.open(root / r.mask) as m:
                mo = np.asarray(m.convert("L")) > MASK_THR
            area = float(mo.mean())
            mb = Image.fromarray((mo * 255).astype(np.uint8), "L")
            mb = cuadrar(mb, "L").resize((IMG_SIZE, IMG_SIZE), Image.NEAREST)
            mb = Image.fromarray(((np.asarray(mb) > MASK_THR) * 255).astype(np.uint8), "L")
            ruta_msk = f"mascaras/{split}/{clase}/{nombre}.png"
            mb.save(SALIDA / ruta_msk)

        filas.append(dict(archivo=nombre, particion=split, clase=clase, plano=r.plane, grupo_hash=int(r.group) if pd.notna(r.group) else "",
                          tiene_mascara=bool(ruta_msk), ruta_imagen=ruta_img, ruta_mascara=ruta_msk,
                          particion_oficial="test" if "_test_" in nombre else "train",
                          duplicado_exacto=bool(r.file in dup), sha256_original=sha.get(r.file, ""),
                          ancho_original=int(ancho.get(r.file, 0)), alto_original=int(alto.get(r.file, 0)),
                          area_tumor_original=area))
        if i % 1000 == 0:
            print(f"  {i}/{len(part)}", flush=True)

    out = pd.DataFrame(filas)
    out.to_csv(SALIDA / "manifest_preparado.csv", index=False)
    print("\nListo. Archivos:", len(out), "| con mascara:", int(out.tiene_mascara.sum()))
    print(pd.crosstab(out.clase, out.particion))
    print("\nSiguiente paso: python verificar_preparado.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
