# Sprint 3 — Evaluación y despliegue

Código del Sprint 3 (HU12 a HU16), siguiendo `docs/PLAN_SPRINT3.md`: evaluación única sobre la prueba oficial,
aplicación web de demostración (prototipo clínico), MLOps básico, informe final y presentación.

> Demostración académica. **No es una herramienta de diagnóstico médico.** La prueba oficial (1.000 imágenes) se
> evalúa **una sola vez**, aquí, y no se usa para elegir nada. El modelo que se despliega se eligió por
> **validación** (semilla 2024 en ambas tareas), no mirando la prueba.

## Flujo completo

```bash
# Entorno (ademas de lo del Sprint 2): onnx, onnxruntime, onnxscript, fastapi, uvicorn, jinja2, python-multipart
pip install -r ../../requirements-sprint2.txt
pip install onnx onnxruntime onnxscript fastapi "uvicorn[standard]" jinja2 python-multipart

# 1. HU12 — evaluacion UNICA sobre la prueba oficial (6 checkpoints del Sprint 2, promedio +- desvio)
python evaluar_prueba_final.py

# 2. Exportar a ONNX los modelos DESPLEGADOS (semilla 2024) y verificar la paridad
python exportar_onnx.py

# 3. HU14 — registro de modelos y metricas (SHA-256, versiones, version del dataset, commit)
python registrar_modelos.py

# 4. Pruebas minimas (paridad, preprocesamiento identico, recorrido de inferencia)
python pruebas.py

# 5. HU13 — aplicacion web de demostracion (prototipo clinico)
python -m uvicorn app.servidor:app --port 8000      # o: iniciar_demo.bat   (Windows)
# abrir http://localhost:8000   (medico / medico123)
```

## HU12 — evaluación única sobre la prueba oficial

Protocolo del plan (sección 5): se evalúan los **6 puntos de control del Sprint 2** (3 semillas × 2 tareas) sobre
la prueba oficial y se reporta **promedio ± desvío (muestral)**. El modelo **desplegado** es el mejor por
validación de cada tarea (**semilla 2024**); los desgloses, la matriz de confusión y el análisis de errores se
hacen con ese modelo. La prueba se evaluó una sola vez y no se cambió nada después de ver los números.

| Tarea | Métrica | Validación (Sprint 2, 3 semillas) | Prueba oficial — desplegado (2024) | Prueba — promedio 3 semillas | Meta |
|---|---|---|---|---|---|
| Clasificación | accuracy | — | **99.10 %** | 99.17 % ± 0.12 % | ≥ 95 % ✓ |
| Clasificación | recall medio | 99.57 % ± 0.15 % | 99.34 % | — | — |
| Clasificación | recall mín. por clase | — | **97.24 % (glioma)** | — | ≥ 90 % ✓ |
| Segmentación | IoU | 80.12 % ± 0.33 % | **80.10 %** | 79.90 % ± 0.19 % | ≥ 70 % ✓ |
| Segmentación | Dice | — | 87.07 % | — | — |

Las tres metas del acta **se cumplen** en la prueba oficial. El desempeño en prueba ≈ validación (no hay colapso
por sobreajuste). Desgloses (riesgo R09): accuracy por tipo de archivo gris/RGB 99.14 % / 99.04 %; IoU gris/RGB
78.87 % / 82.68 %. IoU por clase: glioma 67.97 % (la más difícil), meningioma 89.81 %, hipófisis 80.48 %.

**Subconjunto sin vecino cercano (fuga):** 196 de las 1.000 imágenes de prueba tienen un vecino casi idéntico en
el entrenamiento oficial (correlación de miniaturas 32×32 ≥ 0.98; lista en `test_con_vecino_cercano.csv`).
Quitándolas, las métricas bajan poco: accuracy 98.88 % (n=804) e IoU 78.43 % (n=665) — el efecto de la fuga es
pequeño. El análisis de errores (aciertos y errores, 2 mejores y 2 peores por IoU) está en
`salida_sprint3/prueba_ejemplos_*.png`.

**Nota:** como alternativa documentada (el usuario lo pidió), `reentrenar_final.py` reentrena la configuración
elegida sobre train+val con las épocas fijadas en validación; da 99.30 % / IoU 80.45 % en la prueba. El plan
marca ese reentreno como opcional (P3) y se queda como alternativa; lo desplegado es la semilla 2024.

## HU13 — aplicación web (prototipo clínico)

`app/` es un prototipo de **sistema clínico** con el flujo principal real de **apoyo al diagnóstico en
neuro-oncología** (inicio de sesión → casos → subir una T1 → resultado con clase, probabilidades y contorno →
revisión del médico → informe del caso) y los demás módulos como maqueta. FastAPI + Jinja2 + SQLite; inferencia
con ONNX Runtime en **CPU**; **funciona sin internet** (fuentes del sistema, nada de CDN); diseño blanco y formal.
Detalle en `app/README.md`. Decisión de arquitectura (riesgo R05): backend local en vez de modelo en el navegador,
porque la U-Net pesa ~98 MB en ONNX.

## HU14 — MLOps básico

- `modelos/`: modelos desplegados en ONNX (`clasificador_v1.onnx`, `segmentacion_v1.onnx`) con su **tarjeta de
  modelo** (`*_tarjeta.json`: formato, tamaño, **SHA-256**, paridad, procedencia, versiones de torch/onnxruntime/smp).
- `registro_modelos.json` (se sube a Git): procedencia, SHA-256, métricas de validación y de prueba, **versión del
  dataset** (SHA-256 del manifest + semilla 42) y **commit de Git** de cada modelo.
- **Etiquetas de Git** (versión identificable): `datos-v1.0`, `modelo-clasificador-v1.0`,
  `modelo-segmentacion-v1.0`, `app-v1.0`.
- **Monitoreo** en la propia app (`/admin`): registra cada predicción (clase, probabilidades, confianza, área,
  tiempo, brillo medio, alerta) **sin guardar imágenes ni datos personales**; compara el brillo medio con el de
  entrenamiento como señal simple de deriva.

Los pesos (`.pt`), los modelos (`.onnx`), la base de datos de demostración y las salidas **no se suben a Git** (ver
`.gitignore`): se regeneran con los scripts.

## Estructura

```
preprocesado.py            Preprocesado canonico (gris -> cuadrado -> 256 -> ImageNet), compartido por todo
evaluar_prueba_final.py    HU12: evalua los 6 checkpoints en la prueba (promedio+-desvio), subconjunto sin vecino,
                           analisis de errores; modelo desplegado = semilla 2024
reentrenar_final.py        Alternativa (opcional, P3): reentrena la config elegida sobre train+val
exportar_onnx.py           Exporta a ONNX los modelos desplegados (semilla 2024) y verifica la paridad; SHA-256
registrar_modelos.py       HU14: registro de modelos y metricas versionado (registro_modelos.json)
pruebas.py                 Pruebas minimas (paridad, preprocesamiento identico, recorrido de inferencia)
registro_modelos.json      Registro (se sube a Git; sin pesos)
modelos/                   Artefactos: *.onnx + *_tarjeta.json (ONNX ignorado por Git)
app/                       Aplicacion web (servidor FastAPI, plantillas, estatico, datos_demo); ver app/README.md
iniciar_demo.bat           Script de inicio en Windows
salida_sprint3/            Resultados de la evaluacion, figuras y CSV por imagen (ignorado por Git)
```

## Informe y presentación (HU15, HU16)

En `herramientas/`: `gen_figs_sprint3.py` (figuras reales de la evaluación + capturas de la app),
`build_informe_sprint3.py` → `informe_sprint3.docx` y `build_slides_sprint3.py` → `presentacion_sprint3.pptx`.
Las capturas de la app (`herramientas/capturas_app/`) se toman del sistema en funcionamiento.
