"""Dataset de PyTorch para BRISC 2025 preparado (ver docs/TRASPASO_SPRINT2.md, secciones 4 y 6.6).

Lee manifest_preparado.csv (generado por preparar_dataset.py, Sprint 1) y aplica al cargar:
  - normalizacion de ImageNet (la imagen en gris se repite en 3 canales),
  - aumento de datos opcional, igual en imagen y mascara cuando hay mascara.

No cambia la particion (semilla 42, columna 'particion': train/val/test).
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision.transforms import v2

CLASES = ["glioma", "meningioma", "pituitary", "no_tumor"]
MEDIA = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
DESVIO = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
IMG_SIZE = 256


def raiz_preparado():
    return Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))


def _aumento_clasificacion():
    """Rotacion +-10 grados, escala 0.9-1.1, brillo/contraste +-20%, giro horizontal.
    Sin desplazamientos grandes: la posicion de la hipofisis es informativa (seccion 6.1)."""
    return v2.Compose([
        v2.RandomHorizontalFlip(p=0.5),
        v2.RandomAffine(degrees=10, scale=(0.9, 1.1)),
        v2.ColorJitter(brightness=0.2, contrast=0.2),
    ])


class BriscClasificacion(Dataset):
    """Clasificacion de tipo de tumor (4 clases), cualquier particion."""

    def __init__(self, particion, raiz=None, aumentar=False):
        self.raiz = Path(raiz) if raiz else raiz_preparado()
        m = pd.read_csv(self.raiz / "manifest_preparado.csv")
        self.t = m[m.particion == particion].reset_index(drop=True)
        self.transform = _aumento_clasificacion() if aumentar else None

    def __len__(self):
        return len(self.t)

    def __getitem__(self, i):
        r = self.t.iloc[i]
        with Image.open(self.raiz / r.ruta_imagen) as im:
            x = torch.from_numpy(np.asarray(im, dtype=np.float32) / 255.0).unsqueeze(0).repeat(3, 1, 1)
        if self.transform is not None:
            x = self.transform(x)
        x = (x - MEDIA) / DESVIO
        return x, CLASES.index(r.clase)


class BriscSegmentacion(Dataset):
    """Segmentacion de tumor: solo imagenes con mascara (sin_tumor queda fuera, HU07)."""

    def __init__(self, particion, raiz=None, aumentar=False):
        self.raiz = Path(raiz) if raiz else raiz_preparado()
        m = pd.read_csv(self.raiz / "manifest_preparado.csv")
        self.t = m[(m.particion == particion) & (m.tiene_mascara)].reset_index(drop=True)
        self.aumentar = aumentar

    def __len__(self):
        return len(self.t)

    def __getitem__(self, i):
        r = self.t.iloc[i]
        with Image.open(self.raiz / r.ruta_imagen) as im:
            x = torch.from_numpy(np.asarray(im, dtype=np.float32) / 255.0).unsqueeze(0)
        with Image.open(self.raiz / r.ruta_mascara) as mk:
            y = torch.from_numpy((np.asarray(mk) > 127).astype(np.float32)).unsqueeze(0)
        if self.aumentar:
            angulo = float(torch.empty(1).uniform_(-10, 10))
            escala = float(torch.empty(1).uniform_(0.9, 1.1))
            x = v2.functional.affine(x, angle=angulo, translate=[0, 0], scale=escala, shear=0.0,
                                      interpolation=v2.InterpolationMode.BILINEAR)
            y = v2.functional.affine(y, angle=angulo, translate=[0, 0], scale=escala, shear=0.0,
                                      interpolation=v2.InterpolationMode.NEAREST)
            if torch.rand(1).item() < 0.5:
                x, y = v2.functional.hflip(x), v2.functional.hflip(y)
            x = v2.ColorJitter(brightness=0.2, contrast=0.2)(x)
        x = x.repeat(3, 1, 1)
        x = (x - MEDIA) / DESVIO
        return x, y
