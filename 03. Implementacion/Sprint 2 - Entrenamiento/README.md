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

## Resultados (validación, 22-23 de octubre de 2026)

Entorno: Windows 11, Python 3.12.8, GPU NVIDIA RTX 5060 Laptop (8 GB), `torch==2.11.0+cu128`. Métricas sobre validación
(1.001 imágenes de clasificación, 787 con máscara); **la prueba oficial no se usó** (se evalúa una sola vez en HU12, Sprint 3).
Las 13 corridas completas, con configuración y tiempo, están en [`experimentos.csv`](experimentos.csv).

**Informe y presentación** (generados con datos e imágenes 100 % reales de este Sprint, ver `herramientas/README.md`):
- `herramientas/informe_sprint2.docx` — informe completo (30 encabezados, 16 tablas, 13 figuras): metodología,
  resultados de HU05 a HU09, desglose por clase/plano/tipo de archivo, limitaciones y glosario.
- `herramientas/presentacion_sprint2.pptx` — 18 diapositivas para la Revisión del Sprint 2 (23 oct), mismo
  diseño blanco y formal del Sprint 1.

### Modelo base (HU05/HU06/HU07, semilla 42, config. de partida)

| Tarea | Arquitectura | val_accuracy | val_recall medio | val_IoU | val_Dice |
|---|---|---|---|---|---|
| Clasificación | EfficientNetB0 | 99.5 % | 99.52 % | — | — |
| Clasificación | ResNet50 (2ª arquitectura candidata) | 99.4 % | 99.38 % | — | — |
| Segmentación | U-Net (encoder ResNet34) | — | — | 79.70 % | 86.73 % |

### HU08 — configuraciones probadas (semilla 42, frente al modelo base)

**Clasificador (EfficientNetB0):**

| Configuración | val_recall medio | Δ vs. base |
|---|---|---|
| Base: lr=3e-4, batch=32, con aumento | 99.52 % | — |
| lr=1e-4 | 99.41 % | −0.11 pp |
| **batch=64** ← elegida | **99.62 %** | **+0.10 pp** |
| sin aumento de datos (ablación) | 99.49 % | −0.03 pp |

**U-Net (encoder ResNet34):**

| Configuración | val_IoU | Δ vs. base |
|---|---|---|
| Base: lr=3e-4, batch=8, con aumento | 79.70 % | — |
| **lr=1e-4** ← elegida | **79.78 %** | **+0.08 pp** |
| sin aumento de datos (ablación) | 79.08 % | −0.62 pp |
| batch=16 | 80.09 % | +0.39 pp |

El aumento de datos mejora ambas tareas (quitarlo empeora el resultado en los dos casos). El ajuste de lr/batch
trae mejoras pequeñas (< 1 punto porcentual) frente al modelo base. En la U-Net, `batch=16` dio un resultado a
una sola semilla ligeramente mejor que `lr=1e-4` (80.09 % vs. 79.78 %) — un empate técnico dentro del margen de
variación entre semillas (~0.3 pp, ver abajo). Se mantiene **`lr=1e-4`** como configuración elegida porque ya
tenía las 3 semillas corridas antes de probar `batch=16`; no se repitió el entrenamiento con `batch=16` para no
duplicar cómputo por una diferencia no concluyente.

### Entrenamiento final con 2 semillas adicionales (configuración ganadora de HU08)

| Modelo | Semilla 42 | Semilla 123 | Semilla 2024 | Promedio ± desvío |
|---|---|---|---|---|
| EfficientNetB0, batch=64 (recall medio) | 99.62 % | 99.41 % | 99.69 % | **99.57 % ± 0.12 %** |
| U-Net, lr=1e-4 (IoU) | 79.78 % | 80.14 % | 80.44 % | **80.12 % ± 0.27 %** |

**Modelos elegidos para el Sprint 3:** EfficientNetB0 (batch=64, lr=3e-4) para clasificación y U-Net con
`lr=1e-4` para segmentación — ambos con el mejor promedio multi-semilla y superando las metas del acta
(accuracy ≥ 95 %, recall ≥ 90 % por clase, IoU ≥ 70 %).

### Desglose por plano de corte y tipo de archivo (riesgo R09)

Evaluado con `evaluar_grupos.py` sobre los checkpoints ganadores de semilla 42
(ver `salida_sprint2/*_por_grupo.csv` para el detalle por imagen):

**Clasificador** — accuracy por plano: axial 99.38 %, coronal 99.70 %, sagital 99.71 % (sin diferencias
relevantes). Por tipo de archivo: gris (L) 99.37 %, RGB 99.81 %. **Confirma el hallazgo del Sprint 1:**
el 100 % de las imágenes "sin tumor" en esta validación son RGB (0 en gris) — no hay forma de medir el
recall de "sin tumor" en imágenes grises porque no existen en los datos, no es una falla del modelo.

**U-Net** — IoU por clase: glioma 67.43 % (la más difícil, como se anticipó por su bajo contraste),
pituitary 80.07 %, meningioma 90.12 %. Por plano: axial 77.47 %, coronal 79.66 %, sagital 82.05 %. Por
tipo de archivo: gris (L) 76.50 % vs. RGB 84.83 % — una brecha de ~8 puntos. Como el glioma es
mayoritariamente en escala de grises (hallazgo del Sprint 1: 88 %), **esta brecha parece explicarse en
buena parte por la dificultad propia del glioma y no (solo) por un atajo de procedencia**, pero queda
como punto de atención para el Sprint 3 y para repetir este análisis sobre la prueba oficial en HU12.

Revisando `salida_sprint2/unet_resnet34_*_ejemplos.png`: en 3 de 4 ejemplos la máscara predicha calza bien
con la real; en uno (tumor muy pequeño y alargado) el modelo no predijo nada — consistente con que el
tumor ocupa en mediana 0.9–1.7 % de la imagen.

### Qué falta (fuera de lo técnico, ver `docs/TRASPASO_SPRINT2.md` sección 15.1)

Backlog del Sprint 2 en Trello/Excel, Informe de Estado, Minuta, Registro de Riesgos (agregar R09),
Retrospectiva del Sprint 2 (con el equipo) y el deck de la Revisión del Sprint 2 (HU10).

## Estructura

```
datos.py                  Dataset de PyTorch (manifest_preparado.csv), normalización ImageNet y aumento
modelos.py                EfficientNetB0 / ResNet50 (clasificación) y U-Net (segmentación)
metricas.py                accuracy, recall por clase, F1 macro, matriz de confusión, IoU, Dice
experimentos.py            columnas y utilidades comunes de experimentos.csv
entrenar_clasificador.py   entrena y evalúa el clasificador
entrenar_unet.py           entrena y evalúa la U-Net
evaluar_grupos.py          evalúa un checkpoint por plano de corte y tipo de archivo (riesgo R09)
experimentos.csv           una fila por entrenamiento (HU09)
salida_sprint2/            checkpoints, curvas y figuras (ignorada por Git)
```
