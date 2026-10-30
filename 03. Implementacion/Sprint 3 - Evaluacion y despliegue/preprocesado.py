"""Preprocesado canonico de una imagen de resonancia, identico al del Sprint 1/2.

Se usa en tres lugares para que todos coincidan exactamente:
  - exportar_onnx.py (al verificar la paridad PyTorch vs ONNX),
  - evaluar_prueba.py (evaluacion unica sobre la prueba oficial),
  - app/servidor.py (la interfaz web que recibe imagenes arbitrarias).

Replica lo que hicieron preparar_dataset.py (Sprint 1) y datos.py (Sprint 2):
  imagen -> gris -> relleno a cuadrado con ceros (sin deformar) -> 256x256 bilineal
  -> /255 -> se repite en 3 canales -> normalizacion de ImageNet.
"""
import numpy as np
from PIL import Image

IMG_SIZE = 256
MEDIA = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape(3, 1, 1)
DESVIO = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape(3, 1, 1)
CLASES = ["glioma", "meningioma", "pituitary", "no_tumor"]
CLASES_ES = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Tumor de hipofisis", "no_tumor": "Sin tumor"}


def cuadrar(im, modo="L"):
    """Rellena con ceros hasta un cuadrado, centrando la imagen (igual que preparar_dataset.py)."""
    w, h = im.size
    if w == h:
        return im
    lado = max(w, h)
    lienzo = Image.new(modo, (lado, lado), 0)
    lienzo.paste(im, ((lado - w) // 2, (lado - h) // 2))
    return lienzo


def imagen_a_gris_256(im):
    """PIL.Image arbitraria -> PIL.Image en gris, cuadrada, 256x256 (el 'preparado' del dataset)."""
    g = im.convert("L")
    g = cuadrar(g, "L").resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
    return g


def preprocesar(im):
    """PIL.Image arbitraria -> tensor numpy float32 de forma (1, 3, 256, 256) listo para el modelo.

    Devuelve tambien la imagen en gris 256x256 (uint8) para mostrarla en la interfaz.
    """
    g = imagen_a_gris_256(im)
    arr = np.asarray(g, dtype=np.float32) / 255.0          # (256, 256) en [0, 1]
    x = np.stack([arr, arr, arr], axis=0)                   # (3, 256, 256)
    x = (x - MEDIA) / DESVIO                                # normalizacion ImageNet
    return x[None].astype(np.float32), np.asarray(g, dtype=np.uint8)


def softmax(logits):
    e = np.exp(logits - logits.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def sigmoide(x):
    return 1.0 / (1.0 + np.exp(-x))
