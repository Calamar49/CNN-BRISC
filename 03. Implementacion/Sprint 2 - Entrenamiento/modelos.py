"""Arquitecturas candidatas (ver docs/TRASPASO_SPRINT2.md, secciones 6.1 y 6.2).

Clasificacion: EfficientNetB0 y ResNet50 con transfer learning (pesos de ImageNet).
Segmentacion: U-Net con codificador preentrenado via segmentation-models-pytorch;
si no esta instalado, una U-Net propia con encoder resnet34 de torchvision.
"""
import torch
import torch.nn as nn
from torchvision import models


def crear_clasificador(arquitectura, num_clases=4, preentrenado=True):
    if arquitectura == "efficientnet_b0":
        pesos = models.EfficientNet_B0_Weights.DEFAULT if preentrenado else None
        modelo = models.efficientnet_b0(weights=pesos)
        modelo.classifier[1] = nn.Linear(modelo.classifier[1].in_features, num_clases)
    elif arquitectura == "resnet50":
        pesos = models.ResNet50_Weights.DEFAULT if preentrenado else None
        modelo = models.resnet50(weights=pesos)
        modelo.fc = nn.Linear(modelo.fc.in_features, num_clases)
    else:
        raise ValueError(f"arquitectura desconocida: {arquitectura}")
    return modelo


def crear_unet(encoder="resnet34", preentrenado=True):
    try:
        import segmentation_models_pytorch as smp
        return smp.Unet(encoder_name=encoder, encoder_weights="imagenet" if preentrenado else None,
                         in_channels=3, classes=1)
    except ImportError:
        return _UNetTorchvision(preentrenado=preentrenado)


class _UNetTorchvision(nn.Module):
    """U-Net minima con encoder resnet34 de torchvision (respaldo si no instala segmentation-models-pytorch)."""

    def __init__(self, preentrenado=True):
        super().__init__()
        pesos = models.ResNet34_Weights.DEFAULT if preentrenado else None
        base = models.resnet34(weights=pesos)
        self.enc0 = nn.Sequential(base.conv1, base.bn1, base.relu)  # 256 -> 128, 64 canales
        self.pool = base.maxpool                                     # 128 -> 64
        self.enc1 = base.layer1                                      # 64, 64 canales
        self.enc2 = base.layer2                                      # 32, 128 canales
        self.enc3 = base.layer3                                      # 16, 256 canales
        self.enc4 = base.layer4                                      # 8, 512 canales

        self.up4 = self._bloque_arriba(512, 256, 256)
        self.up3 = self._bloque_arriba(256, 128, 128)
        self.up2 = self._bloque_arriba(128, 64, 64)
        self.up1 = self._bloque_arriba(64, 64, 32)
        self.up0 = nn.ConvTranspose2d(32, 16, 2, stride=2)
        self.salida = nn.Conv2d(16, 1, 1)

    @staticmethod
    def _bloque_arriba(in_c, skip_c, out_c):
        return nn.ModuleDict(dict(
            up=nn.ConvTranspose2d(in_c, out_c, 2, stride=2),
            conv=nn.Sequential(
                nn.Conv2d(out_c + skip_c, out_c, 3, padding=1), nn.ReLU(inplace=True),
                nn.Conv2d(out_c, out_c, 3, padding=1), nn.ReLU(inplace=True),
            ),
        ))

    @staticmethod
    def _subir(bloque, x, skip):
        x = bloque["up"](x)
        x = torch.cat([x, skip], dim=1)
        return bloque["conv"](x)

    def forward(self, x):
        e0 = self.enc0(x)
        p0 = self.pool(e0)
        e1 = self.enc1(p0)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)
        e4 = self.enc4(e3)
        d4 = self._subir(self.up4, e4, e3)
        d3 = self._subir(self.up3, d4, e2)
        d2 = self._subir(self.up2, d3, e1)
        d1 = self._subir(self.up1, d2, e0)
        d0 = self.up0(d1)
        return self.salida(d0)
