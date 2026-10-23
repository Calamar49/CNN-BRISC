# Sprint 2 — Entrenamiento (modelado)

Código del Sprint 2 (HU05 a HU09): clasificador de tipo de tumor y U-Net de segmentación,
sobre el dataset ya preparado en el Sprint 1. Contexto completo en `docs/TRASPASO_SPRINT2.md`.

## Antes de entrenar

1. Dataset preparado y verificado (Sprint 1, carpeta `Sprint 1 - Notebooks`):
   ```bash
   python descargar_brisc.py
   python ejecutar_sprint1.py
   python preparar_dataset.py
   python verificar_preparado.py   # debe terminar con "RESULTADO: todo correcto"
   ```
2. Entorno con PyTorch + CUDA (ver `docs/TRASPASO_SPRINT2.md`, sección 7):
   ```bash
   pip install -r requirements-probado.txt
   pip install torch torchvision --index-url https://download.pytorch.org/whl/<cuXXX>
   pip install segmentation-models-pytorch timm tensorboard
   python -c "import torch; print(torch.cuda.is_available())"   # debe imprimir True
   ```

## Entrenar

```bash
# Clasificador (HU05/HU06) — dos arquitecturas candidatas
python entrenar_clasificador.py --arquitectura efficientnet_b0 --epocas 20 --semilla 42
python entrenar_clasificador.py --arquitectura resnet50 --epocas 20 --semilla 42

# U-Net de segmentación (HU05/HU07)
python entrenar_unet.py --encoder resnet34 --epocas 30 --semilla 42
```

Cada corrida:
- guarda el mejor checkpoint en `salida_sprint2/<id>.pt` (según recall medio de validación en
  clasificación, o IoU de validación en segmentación; parada temprana con paciencia 5),
- escribe la curva de entrenamiento en `salida_sprint2/<id>_curva.csv`,
- en segmentación, guarda ejemplos de máscara predicha frente a la real en `salida_sprint2/<id>_ejemplos.png`,
- añade una fila a `experimentos.csv` con configuración, métricas de validación y tiempo de entrenamiento.

`salida_sprint2/` no se sube a Git (dataset, pesos y figuras pesadas quedan fuera del repositorio).

## Reglas (ver `CLAUDE.md` y `docs/TRASPASO_SPRINT2.md`)

- La partición no se toca (semilla 42, columnas `particion` del manifest). Entrenamiento y
  validación son las únicas particiones usadas aquí; la prueba oficial se evalúa una sola vez
  en el Sprint 3 (HU12).
- `no_tumor` no tiene máscara: queda fuera del entrenamiento de segmentación.
- Para elegir arquitectura, hiperparámetros o época, se usa solo la validación.
- Cada entrenamiento final se repite con 2–3 semillas y se reporta el promedio (sección 6.1).

## Resultados (modelo base, validación, 22-23 de octubre de 2026)

Entorno: Windows 11, Python 3.12.8, GPU NVIDIA RTX 5060 Laptop (8 GB), `torch==2.11.0+cu128`. Semilla 42, aumento de datos activado. Métricas sobre validación (1.001 imágenes de clasificación, 787 con máscara); **la prueba oficial no se usó** (se evalúa una sola vez en HU12, Sprint 3).

| Tarea | Arquitectura | Época óptima | val_accuracy | val_recall medio | val_F1 macro | val_IoU | val_Dice | Tiempo |
|---|---|---|---|---|---|---|---|---|
| Clasificación (HU06) | EfficientNetB0 | 8/13 | 99.5 % | 99.52 % | 99.50 % | — | — | 4.9 min |
| Clasificación (HU06) | ResNet50 | 15/20 | 99.4 % | 99.38 % | 99.40 % | — | — | 10.6 min |
| Segmentación (HU07) | U-Net (encoder ResNet34) | 25/30 | — | — | — | 79.70 % | 86.73 % | 18.7 min |

- Ambas arquitecturas de clasificación superan la meta del acta (accuracy ≥ 95 %, recall ≥ 90 % por clase) y el recall por clase de EfficientNetB0 fue parejo (98.87 %–100 %, ver `experimentos.csv`). **EfficientNetB0 es el modelo elegido** por mejor recall medio y menor tiempo de entrenamiento.
- La U-Net supera la meta (IoU ≥ 70 %) y la referencia del artículo de BRISC (U-Net, 75.7 % mIoU), aunque esa cifra es del artículo, no comparable en igualdad de condiciones (otra partición).
- Revisando `salida_sprint2/unet_resnet34_*_ejemplos.png`: en 3 de 4 ejemplos la máscara predicha calza bien con la real; en uno (tumor muy pequeño y alargado) el modelo no predijo nada — consistente con el hallazgo del Sprint 1 de que el tumor ocupa en mediana 0.9–1.7 % de la imagen y el glioma tiene contraste casi igual al tejido.
- **Pendiente antes de cerrar HU06–HU09** (ver sección 5 del traspaso): ajustar hiperparámetros con al menos 3 configuraciones (HU08), repetir el entrenamiento final con 2–3 semillas, reportar métricas por plano de corte y por tipo de archivo (gris/RGB) para vigilar el atajo R09, y completar la tabla de experimentos en el informe (HU09).

## Estructura

```
datos.py                  Dataset de PyTorch (manifest_preparado.csv), normalización ImageNet y aumento
modelos.py                EfficientNetB0 / ResNet50 (clasificación) y U-Net (segmentación)
metricas.py                accuracy, recall por clase, F1 macro, matriz de confusión, IoU, Dice
experimentos.py            columnas y utilidades comunes de experimentos.csv
entrenar_clasificador.py   entrena y evalúa el clasificador
entrenar_unet.py           entrena y evalúa la U-Net
experimentos.csv           una fila por entrenamiento (HU09)
salida_sprint2/            checkpoints, curvas y figuras (ignorada por Git)
```
