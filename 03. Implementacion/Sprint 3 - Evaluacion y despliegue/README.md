# Sprint 3 — Evaluación y despliegue

Código del Sprint 3 (HU12 a HU16): evaluación única sobre la prueba oficial, aplicación web de demostración,
MLOps básico (registro de modelos), informe final y presentación. Contexto en `docs/TRASPASO_SPRINT2.md`
(secciones 6.4 y 10) y `CLAUDE.md`.

> Demostración académica. **No es una herramienta de diagnóstico médico.** La prueba oficial (1.000 imágenes)
> se evalúa **una sola vez**, aquí, y no se usa para elegir nada.

## Flujo completo

```bash
# 0. Entorno (ademas de lo del Sprint 2): onnx, onnxruntime, fastapi, uvicorn, onnxscript
pip install onnx onnxruntime onnxscript fastapi "uvicorn[standard]" python-multipart

# 1. Reentrenar la configuracion elegida sobre train+val (epocas fijadas en validacion)
python reentrenar_final.py --tarea clasificacion   # EfficientNetB0 batch=64, 10 epocas
python reentrenar_final.py --tarea segmentacion    # U-Net lr=1e-4, 26 epocas

# 2. Exportar a ONNX (verifica la paridad PyTorch vs ONNX en imagenes reales)
python exportar_onnx.py

# 3. HU12: evaluacion UNICA sobre la prueba oficial
python evaluar_prueba.py                           # escribe salida_sprint3/evaluacion_prueba.json y figuras

# 4. HU14: registro de modelos y metricas
python registrar_modelos.py                        # escribe registro_modelos.json (si se sube a Git)

# 5. HU13: aplicacion web de demostracion
python -m uvicorn app.servidor:app --port 8000     # abrir http://localhost:8000
```

## Por qué se reentrena antes de evaluar (HU12)

En los Sprints 1 y 2 la partición fue 3.999 entrenamiento / 1.001 validación / 1.000 prueba. La validación sirvió
para **elegir** arquitectura, hiperparámetros y época; la prueba no se tocó. Para el modelo final que se evalúa y
se despliega, se reentrena la configuración elegida sobre **entrenamiento + validación (5.000 imágenes de
clasificación; 3.933 con máscara)**, con el número de épocas **fijado de antemano** en validación (sin parada
temprana, porque ya no queda validación para vigilar):

- Clasificador EfficientNetB0 (batch=64, lr=3e-4): épocas óptimas en validación 6/14/10 → se fija **10**.
- U-Net ResNet34 (lr=1e-4): épocas óptimas 28/25/24 → se fija **26**.

**Advertencia honesta:** el Sprint 1 encontró que 113–123 de las 1.000 imágenes de prueba tienen un vecino casi
idéntico en el entrenamiento oficial. Como el modelo final se reentrena con train+val, la cifra de prueba puede
estar algo inflada; se reporta junto al resultado.

## La aplicación web (HU13)

`app/servidor.py` (FastAPI) sirve los modelos ONNX con onnxruntime; `app/estatico/` es la interfaz (HTML/CSS/JS
vanilla, sin framework). Se sube una resonancia y el sistema predice el tipo de tumor y marca su contorno. El
diseño es un **visor de radiología**: imagen en gris sobre fondo oscuro, máscara de tumor como overlay coral,
lecturas en tipografía monoespaciada. Trae ejemplos reales de la prueba oficial para probar sin subir nada.

Elección de arquitectura (riesgo R05, tamaño del modelo en el navegador): se optó por un **backend local** con
onnxruntime en vez de correr los modelos en el navegador, porque la U-Net pesa ~98 MB en ONNX y descargarla en el
cliente sería lento y frágil. El backend sirve el modelo y el navegador solo recibe la imagen y los resultados.

## MLOps básico (HU14)

`modelos/` es el registro de modelos: cada modelo final en ONNX (`*.onnx`) con su **tarjeta de modelo**
(`*_tarjeta.json`: formato, tamaño, forma de entrada/salida, paridad PyTorch↔ONNX, procedencia del entrenamiento).
`registro_modelos.json` (en la raíz de esta carpeta) reúne, versionado y con el commit de Git, la procedencia,
la métrica de validación del Sprint 2 y la métrica en la prueba oficial del Sprint 3 de cada modelo.

Los pesos (`*.pt`), los modelos (`*.onnx`) y las salidas pesadas **no se suben a Git** (ver `.gitignore`): se
regeneran con los scripts. Lo versionado es el código, las tarjetas de modelo y el registro de métricas.

## Informe y presentación (HU15, HU16)

Generados con datos e imágenes reales de este Sprint (ver `herramientas/README.md`):
- `herramientas/informe_sprint3.docx` — informe final (30 encabezados, 18 tablas, 9 imágenes): evaluación en la
  prueba oficial, la aplicación web con capturas reales, MLOps, limitaciones y glosario.
- `herramientas/presentacion_sprint3.pptx` — 15 diapositivas para la Revisión del Sprint 3.
- `herramientas/gen_figs_sprint3.py` genera las figuras de evaluación (de `salida_sprint3/evaluacion_prueba.json`)
  y reúne las capturas de la app. Las **capturas de la aplicación** (`herramientas/capturas_app/app_*.jpg`) se toman
  a mano del visor en funcionamiento (levantar la app, abrir un ejemplo, capturar); no se regeneran por script y no
  se suben a Git. El informe y el deck sí se regeneran con sus scripts una vez que esas imágenes existen.

## Resultado en la prueba oficial (HU12, evaluado una sola vez)

| Tarea | Métrica | Validación (Sprint 2) | Prueba oficial (HU12) | Meta del acta |
|---|---|---|---|---|
| Clasificación | accuracy | — | 99.30 % | ≥ 95 % |
| Clasificación | recall medio | 99.57 % ± 0.12 % | 99.34 % | ≥ 90 % por clase |
| Clasificación | recall mínimo por clase | — | 98.03 % (glioma) | ≥ 90 % |
| Segmentación | IoU | 80.12 % ± 0.27 % | 80.45 % | ≥ 70 % |
| Segmentación | Dice | — | 87.34 % | — |

Las tres metas del acta se superan en la prueba oficial. El desempeño en prueba ≈ validación (no hay colapso por
sobreajuste). Se reporta la advertencia de las 113–123 imágenes de prueba con vecino casi idéntico en entrenamiento.

## Estructura

```
preprocesado.py            Preprocesado canonico (gris -> cuadrado -> 256 -> ImageNet), compartido por todo
reentrenar_final.py        Reentrena la config elegida sobre train+val, epocas fijas (modelo final)
exportar_onnx.py           Exporta los .pt finales a ONNX y verifica la paridad en imagenes reales
evaluar_prueba.py          HU12: evaluacion unica sobre la prueba oficial (metricas, figuras, CSV por imagen)
registrar_modelos.py       HU14: registro de modelos y metricas versionado (registro_modelos.json)
registro_modelos.json      Registro (se sube a Git; sin pesos)
modelos/                   Registro de artefactos: *.onnx + *_tarjeta.json (ONNX ignorado por Git)
app/
  servidor.py              Backend FastAPI (onnxruntime)
  estatico/                Interfaz web (index.html, estilos.css, app.js) + ejemplos/ (ignorado por Git)
salida_sprint3/            Checkpoints finales, metricas de prueba y figuras (ignorado por Git)
```
