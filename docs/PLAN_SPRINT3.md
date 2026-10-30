# Plan del Sprint 3: evaluación, despliegue y cierre del proyecto

Escrito el **29 de octubre de 2026** para ti, que lo vas a ejecutar con tu Claude. **Tú hiciste el Sprint 2 y tienes los modelos y el entorno, así que tú ejecutas la prioridad P0 y la P1 (sección 4).** Este plan cubre todo el Sprint 3 (HU12 a HU17), el sistema web con el flujo principal de apoyo al diagnóstico acordado con el equipo, el MLOps básico y el cierre de gestión.
Convención: **[decidido]** lo acordado con el equipo, **[criterio Trello]** lo que ya figura como criterio de aceptación, **[propuesta]** lo que se sugiere y debes confirmar con el equipo.

## 0. Cómo empezar
1. Haz `git pull` del repositorio https://github.com/Calamar49/CNN-BRISC y ábrelo con Claude Code (lee `CLAUDE.md` solo).
2. Primer mensaje sugerido: *«Lee CLAUDE.md, docs/TRASPASO_SPRINT2.md y docs/PLAN_SPRINT3.md. Empieza por la sección 4 (qué hacer primero). No inventes datos, no uses la prueba oficial antes de HU12 y pregúntame lo que no esté claro.»*
3. **Confirma con el docente y con tu equipo las fechas reales.** Según el Gantt: presentación final **30 oct**, margen **31 oct** (solo imprevistos), entrega límite **2 nov 2026**. Hoy es 29 oct: casi todo es urgente, por eso el plan tiene prioridades (sección 4).

## 1. Estado de partida
| Parte | Estado |
|---|---|
| Sprint 1 (HU01–HU04) | Terminado: negocio, datos y preparación. Informe y presentación hechos. |
| Sprint 2 técnico (HU05–HU09) | **Hecho en el repo:** pipeline, 13 entrenamientos en `experimentos.csv`, modelos elegidos, desglose por plano y tipo de archivo (R09). Todo con **validación**; la prueba oficial no se tocó. |
| Informe y presentación del Sprint 2 | Los tienes tú (`informe_sprint2.docx`, `presentacion_sprint2.pptx`); **no están en el repo** (el `.gitignore` los excluye). **Súbelos** a `03. Implementacion/` y `04. Revision y retrospectiva/`. |
| Gestión del Sprint 2 | **Sin hacer:** Trello (HU06–HU17 en «Product Backlog», lista «Sprint 2» vacía), Backlog del Sprint 2 (Excel con ejemplos de plantilla), Informe de Estado, Minuta, R09, Retrospectiva. |
| Pesos de los modelos | Están en tu carpeta `salida_sprint2/` (Git los ignora). Tú exportas los modelos a `.onnx`; si alguno de tus compañeros necesita correr la app, le entregas los `.onnx` y `registro_modelos.json`. |

### Modelos elegidos en el Sprint 2 (de `experimentos.csv`; métricas de validación)
| Tarea | Configuración | Corridas (`salida_sprint2/<id>.pt`) | Resultado en validación |
|---|---|---|---|
| Clasificación | EfficientNetB0, batch 64, lr 3e-4, con aumento | `clf_efficientnet_b0_20261023_002839` (semilla 42), `..._004200` (123), `..._004900` (2024) | Recall medio 99,62 % / 99,40 % / 99,69 % → **99,57 % ± 0,15 %** (desvío muestral) |
| Segmentación | U-Net con encoder ResNet34, lr 1e-4, batch 8, con aumento | `unet_resnet34_20261023_002334` (42), `..._005823` (123), `..._005828` (2024) | IoU 79,78 % / 80,14 % / 80,44 % → **80,12 % ± 0,33 %** |

Formato de los puntos de control: clasificador `{"modelo": state_dict, "arquitectura", "epoca", "metricas"}`; U-Net `{"modelo": state_dict, "encoder", "epoca", "val_iou", "val_dice"}`. Se reconstruyen con `modelos.py` (`crear_clasificador`, `crear_unet`). **La U-Net debe reconstruirse con `segmentation-models-pytorch`** (el mismo con que se entrenó), no con el respaldo de torchvision, porque los nombres de los pesos difieren.

## 2. Qué hay que entregar (historias del Sprint 3)
| HU | Qué | Fecha Gantt | Puntos | Criterios de aceptación en Trello |
|---|---|---|---|---|
| HU12 | Evaluar los modelos en la prueba oficial | 26 oct | 5 | Accuracy y recall por clase, e IoU en imágenes con tumor, **calculados una sola vez** sobre la prueba oficial · resultados comparados con las metas (accuracy ≥ 95 %, recall ≥ 90 %, IoU ≥ 70 %) · matriz de confusión y ejemplos de aciertos y errores · limitaciones declaradas (sin ID de paciente, solo T1 con contraste) |
| HU13 | Construir la aplicación de demostración | 26–28 oct | 8 | Permite subir una imagen y muestra la clase y la probabilidad · superpone la máscara cuando hay tumor · los modelos se cargan desde **archivos exportados**, no escritos en el código · aviso visible de que es una demostración académica y no un diagnóstico |
| HU14 | MLOps básico: versionado y monitoreo | 27–28 oct | 5 | Modelos y datos con versión identificable (por ejemplo, etiqueta en Git) · pasos para reproducir el entrenamiento documentados · monitoreo básico definido (por ejemplo, registro de las probabilidades predichas) |
| HU15 | Redactar el informe final | 26–28 oct | 5 | Incluye todas las fases (negocio, datos, modelado, evaluación y despliegue) · resultados con las métricas y la tabla de experimentos · limitaciones y consideraciones éticas · **revisado por los 4 integrantes** |
| HU16 | Preparar la exposición, la demo y el ensayo general | 28–29 oct | 3 | Diapositivas listas y partes repartidas entre los 4 integrantes · demo probada y con plan alternativo si falla internet · ensayo general (el 29 de octubre) |
| HU17 | Presentación final | 30 oct | 2 | Exposición y demo realizadas el 30 de octubre · entrega final (informe y archivos) lista antes del 2 de noviembre · el 31 de octubre queda reservado solo para imprevistos |

## 3. Decisiones tomadas con el equipo para el despliegue [decidido]
- El despliegue será un **sistema web tradicional** (servidor + base de datos), pensado como **prototipo para clínicas privadas**, con varios módulos.
- **El flujo principal debe estar completo y verse profesional:** el médico sube una resonancia T1 en el módulo de neuro-oncología y ve cómo funcionan el modelo que **clasifica** y el que **segmenta**, como **apoyo al diagnóstico**.
- **Los demás módulos son maqueta**, sin funciones reales.
- Lenguaje: decir «apoyo al diagnóstico» o «sugerencia del sistema», **nunca** «el sistema diagnostica».

### Por confirmar con el docente [propuesta]
- El acta dice «aplicación web de apoyo académico». Conviene ajustar la redacción del «¿para dónde?» a algo como *«un prototipo de sistema web para clínicas, con un módulo de apoyo al diagnóstico en neuro-oncología (demostración académica)»*. **El proyecto sigue sin cliente real y sin datos de pacientes reales.**
- Hay secciones del informe del Sprint 1 (2.3 y 2.4) con grupos hipotéticos y un escenario de clínica con supuestos; las diapositivas ya no los tienen. Decidir si se quitan del informe final.

## 4. Qué hacer primero (orden y prioridades)
**P0, imprescindible para la presentación del 30 oct**
1. Localiza tus `.pt` (en `salida_sprint2/`) y **ejecuta HU12** (sección 5): una sola evaluación en la prueba oficial. *(1 a 2 h)*
2. **Exporta los modelos a ONNX** y verifica que dan lo mismo que PyTorch (sección 6.2). *(1 h)*
3. **Construye el flujo principal de la aplicación, funcionando en local y sin internet** (sección 6.3 a 6.6), con 5 o 6 imágenes de ejemplo. *(el resto del día)*
4. **Actualiza las diapositivas finales** con los resultados de prueba y la demo, y reparte la exposición entre los 4. *(en paralelo)*
5. **Prueba la demo, prepara el plan alternativo** (capturas o video) y haz el **ensayo general**. *(antes de dormir)*

**P1, después de la presentación (31 oct es solo para imprevistos; 1 y 2 nov para esto)**
6. **Haz el MLOps básico (HU14):** registro de modelos, etiquetas en Git, registro de predicciones, README de reproducción.
7. **Redacta el informe final** (HU15) y consigue que lo revisen los 4.
8. **Cierra la gestión:** Trello, Excel, Informe de Estado, Minuta, Riesgos, Retrospectivas y Acta de Cierre (sección 9).

**P2, si sobra tiempo:** maqueta de los otros módulos, ficha del modelo dentro de la app, informe PDF del caso, página de monitoreo.
**P3, recortar sin culpa:** publicación en línea, versión solo-navegador con `onnxruntime-web`, soporte DICOM, HU11 (multitarea) y el reentrenamiento con 5.000 imágenes.

**Reparto [decidido]: tú ejecutas P0 y P1.** Tus 3 compañeros no se quedan sin tareas: **revisan el informe final** (HU15 exige la revisión de los 4), **preparan y ensayan su parte de la exposición** (HU16) y hacen contigo la gestión que solo el equipo puede hacer (retrospectivas, minutas y Trello con revisión cruzada). **Pídeselo:** tú no puedes marcar esos criterios solo. Si te saturas, lo primero que delegas es la maqueta de módulos y las diapositivas. HU12 y la exportación van primero porque la app depende de ellas.

## 5. HU12: evaluación única en la prueba oficial
**Regla de oro:** la prueba se evalúa **una vez**. No se cambia nada después de ver los números: ni arquitectura, ni umbrales, ni se reentrena para mejorar la prueba. Se reporta lo que salga, aunque no cumpla las metas.

**Qué hacer** (script nuevo `evaluar_prueba.py` en `03. Implementacion/Sprint 3 - Evaluacion/`, reutilizando `datos.py` con `particion="test"`, `metricas.py` y la lógica de `evaluar_grupos.py`):
1. Cargar los **6 puntos de control** de la sección 1 (3 semillas por tarea) y evaluarlos en la prueba. Reportar **promedio ± desvío** (indicar que el desvío es muestral) y el resultado de cada semilla.
2. **Clasificación (1.000 imágenes):** accuracy, recall por clase, F1 macro y **matriz de confusión**.
3. **Segmentación (860 imágenes con tumor):** IoU y Dice, en total y por clase (glioma, meningioma, hipófisis).
4. **Desglose por plano de corte y por tipo de archivo** (gris o RGB; la columna `mode` está en `salida_sprint1/perfil_datos/perfil_imagenes.csv`). Añadir la opción `--particion test` a `evaluar_grupos.py`.
5. **Análisis de errores:** lista de imágenes mal clasificadas con su clase real, la predicha y la probabilidad; 4 a 6 ejemplos visuales de aciertos y de errores (clasificación y segmentación).
6. **Subconjunto sin vecino cercano:** 113 a 123 de las 1.000 imágenes de prueba tienen un vecino casi idéntico en el entrenamiento. Repetir las métricas **solo con las imágenes de prueba sin vecino cercano**, calculado como en el notebook `02_HU03` (miniaturas de 32×32, correlación ≥ 0,98 → 123 imágenes) y guardar la lista en `test_con_vecino_cercano.csv`. Es la forma honesta de acotar el efecto de la fuga.
7. **Comparar con las metas del acta:** accuracy ≥ 95 %, recall ≥ 90 % en cada clase, IoU ≥ 70 %. Decir claramente «cumple» o «no cumple» por cada una.
8. Guardar todo en `salida_sprint3/` (CSV, matriz de confusión, figuras) y subir **las tablas finales** al repo (no los pesos).
9. Declarar limitaciones: sin ID de paciente, solo T1 con contraste, un solo dataset, la prueba difiere moderadamente del entrenamiento, posible atajo por procedencia (R09).

**Qué modelo se despliega:** el mejor por **validación** de cada tarea (semilla 2024 en ambos casos: 99,69 % y 80,44 %). **No elegir el modelo mirando la prueba.**

## 6. HU13: el sistema web y el flujo principal de apoyo al diagnóstico

### 6.1 Estructura sugerida [propuesta]
```
03. Implementacion/Sprint 3 - Aplicacion/
├─ exportar_onnx.py          exporta y verifica los modelos
├─ modelos/                  clasificador_v1.onnx, segmentacion_v1.onnx, registro_modelos.json
├─ app/                      la aplicación web (servidor, plantillas, estilos locales, base de datos de demostración)
├─ datos_demo/               pacientes ficticios y 5 o 6 imágenes de ejemplo (de VALIDACIÓN)
├─ requirements-app.txt      versiones fijadas
└─ README.md                 cómo instalar, ejecutar y probar
```
**Tecnología:** si el equipo conoce **Django**, usarlo (ya trae inicio de sesión, panel de administración, base de datos y módulos). Si no, **FastAPI + Jinja2 + SQLite**. Inferencia con **ONNX Runtime en CPU**: corre en cualquier computadora y sin GPU. **Sin dependencias de internet** (CSS, fuentes y JavaScript en archivos locales, no desde CDN), porque la demo debe poder correr sin conexión.

### 6.2 Exportar a ONNX (`exportar_onnx.py`)
```python
import torch
from modelos import crear_clasificador, crear_unet   # de "Sprint 2 - Entrenamiento"

ck = torch.load("salida_sprint2/clf_efficientnet_b0_20261023_004900.pt", map_location="cpu", weights_only=False)
m = crear_clasificador(ck["arquitectura"], preentrenado=False); m.load_state_dict(ck["modelo"]); m.eval()
torch.onnx.export(m, torch.zeros(1, 3, 256, 256), "modelos/clasificador_v1.onnx", input_names=["imagen"],
                  output_names=["logits"], opset_version=17, dynamic_axes={"imagen": {0: "lote"}, "logits": {0: "lote"}})

ck = torch.load("salida_sprint2/unet_resnet34_20261023_005828.pt", map_location="cpu", weights_only=False)
u = crear_unet(ck["encoder"], preentrenado=False); u.load_state_dict(ck["modelo"]); u.eval()   # requiere segmentation-models-pytorch
torch.onnx.export(u, torch.zeros(1, 3, 256, 256), "modelos/segmentacion_v1.onnx", input_names=["imagen"],
                  output_names=["logits_mascara"], opset_version=17, dynamic_axes={"imagen": {0: "lote"}, "logits_mascara": {0: "lote"}})
```
**Verificar la paridad** con 20 imágenes de validación: la diferencia máxima entre PyTorch y ONNX Runtime debe ser muy pequeña (por ejemplo, < 1e-3 en los logits) y las máscaras binarias deben coincidir. Si la exportación de la U-Net falla, probar otro `opset_version` y comprobar la versión de `torch` y de `segmentation-models-pytorch`.
**Tamaño:** estimo ~16 MB el clasificador y ~100 MB la U-Net en fp32 (**verificar con los archivos reales**). GitHub rechaza archivos de más de 100 MB: si la U-Net lo supera, convertir a fp16, usar Git LFS o publicar el modelo en un *Release* de GitHub y dejar en el repo solo `registro_modelos.json` con el enlace y el SHA-256.

### 6.3 Preprocesamiento y postprocesamiento (deben ser **idénticos** al entrenamiento)
```python
import numpy as np
from PIL import Image
MEDIA = np.array([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None]
DESVIO = np.array([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None]

def preparar(img):                                      # img: PIL.Image
    g = img.convert("L"); w, h = g.size; lado = max(w, h)
    lienzo = Image.new("L", (lado, lado), 0); lienzo.paste(g, ((lado - w) // 2, (lado - h) // 2))   # relleno a cuadrado
    x = np.asarray(lienzo.resize((256, 256), Image.BILINEAR), dtype=np.float32) / 255.0
    x = (np.stack([x] * 3) - MEDIA) / DESVIO                                                          # 3 x 256 x 256
    return x[None], (w, h, lado)

# clasificación: probabilidades = softmax(logits); clases = ["glioma", "meningioma", "pituitary", "no_tumor"]
# segmentación: p = sigmoid(logits_mascara)[0, 0]; mascara = p > 0.5 (256 x 256)
#   volver al tamaño original: redimensionar a (lado, lado) con NEAREST y recortar el relleno
#   caja = ((lado - w) // 2, (lado - h) // 2, (lado - w) // 2 + w, (lado - h) // 2 + h)
```
**Regla de decisión [propuesta]:**
- Si el clasificador predice **«sin tumor»**, **no se muestra máscara** (la U-Net nunca vio imágenes sin tumor).
- Si la probabilidad más alta es **< 0,80**, mostrar «**confianza baja: requiere revisión del médico**» (el umbral 0,80 es una propuesta, no está medido; documentarlo así).
- Mostrar el **área del tumor** como porcentaje de la imagen y las 4 probabilidades.
- **Validar la entrada:** formato PNG o JPG, tamaño razonable, y advertir si el brillo medio está fuera del rango visto en entrenamiento (el brillo medio del cerebro fue de ~36 a ~161 sobre 255) o si la imagen no parece una T1 con contraste. El modelo solo conoce ese tipo de imagen.

### 6.4 El flujo principal, pantalla por pantalla (debe estar completo y pulido)
1. **Inicio de sesión** (simulado) como médico; existe también un rol administrador.
2. **Lista de casos** con pacientes **ficticios**.
3. **Caso:** datos del paciente ficticio y botón «Nuevo estudio de neuro-oncología».
4. **Subir la resonancia T1** con las validaciones de la sección 6.3.
5. **Procesando**, con indicador de progreso (la inferencia en CPU debería tardar pocos segundos; medirlo).
6. **Resultado:** imagen con la máscara superpuesta y control de opacidad, clase sugerida con las 4 probabilidades, área del tumor y alerta de confianza baja.
7. **Revisión del médico:** acepta o corrige la sugerencia y escribe un comentario.
8. **Informe del caso** (vista previa o PDF) con fecha, usuario, resultado, **versión de los modelos** y el aviso de demostración.
9. **Ficha de los modelos:** datos de entrenamiento, métricas (validación y, tras HU12, prueba), limitaciones y versión.

**Aviso visible en todas las pantallas** (criterio de Trello): *«Demostración académica. Apoyo al diagnóstico, no es un diagnóstico médico.»*

### 6.5 Los otros módulos: maqueta [decidido]
Menú lateral con **Pacientes, Agenda, Laboratorio, Imagenología general, Facturación, Reportes y Configuración**. Cada uno es una pantalla estática con datos ficticios y una etiqueta visible «**Maqueta, no implementado**». Usar el mismo diseño que el flujo principal. No gastar tiempo en funciones reales.

### 6.6 Calidad visual y de uso
- Diseño blanco y formal (el estilo de las presentaciones; paleta `#1F3864 #5B84B1 #2B7A8B #8FB89A #9AA5B1`; sin naranja), todo en español.
- Estados de carga y de error cuidados; mensajes claros; nada que se rompa en la demo.
- **Datos de demostración:** pacientes inventados (declarados como ficticios) y 5 o 6 imágenes de **validación** (no de prueba) elegidas con cuidado, incluyendo **un caso donde el modelo duda o se equivoca**, para mostrar honestidad.
- Trazabilidad: guardar quién subió el estudio, cuándo y con qué versión del modelo.

### 6.7 Pruebas antes de presentar
Lista de comprobación: instalar en un entorno limpio con `requirements-app.txt` · ejecutar **sin internet** · recorrer el flujo completo con las 5 o 6 imágenes · medir el tiempo por imagen · probar un archivo inválido · probar en la computadora donde se presentará. **Plan alternativo:** capturas de pantalla y un video corto del flujo completo.

### 6.8 Criterios de aceptación propios [propuesta]
Se puede recorrer el flujo 1 a 8 sin errores · los modelos se cargan desde `modelos/*.onnx` · la paridad con PyTorch está verificada y registrada · el aviso de demostración aparece en todas las pantallas · funciona sin internet · el README permite instalarla desde cero.

## 7. HU14: MLOps básico
- **Versionado de modelos:** `modelos/registro_modelos.json` con, por modelo: nombre, tarea, arquitectura, `id` de la corrida, semilla, archivo, **SHA-256**, tamaño, fecha, métricas de validación y de prueba, **commit de Git**, versiones de `torch`, `onnxruntime` y `segmentation-models-pytorch`.
- **Versionado de datos:** `manifest_preparado.csv` con su SHA-256 y la semilla 42; registrar la versión del dataset.
- **Etiquetas de Git:** `datos-v1.0`, `modelo-clasificador-v1.0`, `modelo-segmentacion-v1.0` y `app-v1.0` [criterio Trello: versión identificable].
- **Reproducir el entrenamiento:** el README del Sprint 2 ya trae los comandos; añadir el entorno (versiones con `pip freeze`) y las semillas [criterio Trello].
- **Monitoreo básico** [criterio Trello]: registrar en la base de datos, **sin guardar imágenes ni datos personales**, cada predicción con: fecha, versión del modelo, clase predicha, las 4 probabilidades, confianza, área del tumor, tiempo de respuesta, brillo medio de la entrada y si hubo alerta de confianza baja. Una página de administrador con el total de predicciones, la distribución de clases, la confianza media, el porcentaje de alertas y el tiempo p95. Comparar el brillo medio de las entradas con el del entrenamiento como señal simple de deriva.

## 8. HU15 y HU16–HU17: informe, exposición y entrega
### 8.1 Informe final (HU15)
Reutilizar `03. Implementacion/Informe del Sprint 1.docx`, `informe_sprint2.docx` y los generadores de `herramientas/`. Esquema [propuesta]: 1 Resumen · 2 Comprensión del negocio · 3 Comprensión de los datos · 4 Preparación de los datos · 5 Modelado (Sprint 2, con la **tabla de experimentos**) · 6 **Evaluación** (HU12) · 7 **Despliegue y MLOps** (HU13 y HU14, con capturas de la app) · 8 **Limitaciones y consideraciones éticas** · 9 Conclusiones y trabajo futuro · anexos (reproducibilidad, enlaces, citas). Cumplir los criterios: todas las fases, métricas y tabla de experimentos, limitaciones y ética, **revisado por los 4 integrantes** (agregar una tabla de revisión con fecha).
**Cuidados:** no inventar cifras; distinguir lo medido de lo del artículo; citar BRISC (licencia CC BY 4.0); cotejar las cifras de referencia con la versión publicada en *Scientific Data*; la consideración ética debe decir que es una demostración, que no se usó ningún dato de pacientes reales y que no sustituye al médico.

### 8.2 Exposición (HU16) y presentación final (HU17)
- Diapositivas con el mismo diseño blanco (base: `herramientas/deck_light.py` y `build_slides_sprint2.py`). Estructura [propuesta]: problema y metodología · etapas 1 a 3 (resumen) · Sprint 2 (modelos y resultados de validación) · **Sprint 3: evaluación en la prueba** · **demo del sistema** · MLOps · limitaciones y ética · conclusiones y trabajo futuro.
- **Repartir la exposición entre los 4 en bloques seguidos y equitativos**, con «Expone: nombre» en cada diapositiva.
- **Guion de la demo (2 a 3 min):** iniciar sesión → abrir un caso → subir una T1 → ver clase, probabilidades y máscara → revisión del médico → informe → mostrar la ficha del modelo y un caso difícil.
- **Ensayo general** con cronómetro y con el plan alternativo preparado.

## 9. Gestión Scrum y cierre (la haces tú, con tus compañeros donde se indica)
| Entregable | Dónde | Qué hacer |
|---|---|---|
| Trello | tablero (`CLAUDE.md`) | Mueve HU06–HU11 a «Sprint 2» y HU12–HU17 a «Sprint 3», asigna responsables, y marca los criterios **solo cuando estén cumplidos y revisados por otro integrante**; deja comentarios con los resultados |
| Backlog del Sprint | `02. Planificacion/Backlog del Sprint.xlsx` | Reemplaza los ejemplos de la hoja «Sprint 2» por las tareas reales; crea la hoja «Sprint 3» copiando «Plantilla Sprint» |
| Hojas «Sprints» | `Backlog del Producto.xlsx` y `Backlog Detallado del Producto.xlsx` | Sustituye las fechas de la plantilla (2018) por los 3 sprints reales |
| Informe de Estado y Minutas | `03. Implementacion/` | Actualiza con el avance real; usa las fechas, el lugar y los acuerdos reales del equipo (no los inventes) |
| Registro de Riesgos e Impedimentos | `02. Planificacion/`, `03. Implementacion/` | Agrega R09 y los riesgos nuevos; anota los impedimentos reales |
| Cronograma (CSV del Gantt) | `02. Planificacion/` | Actualiza la columna Progress |
| Retrospectivas | `04. Revision y retrospectiva/` y `05. Lanzamiento/Retrospectiva del Proyecto.pptx` | Hazlas **con tus 3 compañeros**; no escribas respuestas por ellos |
| Acta de Cierre | `06. Cierre/Acta de Cierre de Proyecto.docx` | Llénala al final con datos reales; es una plantilla sin llenar |
| Presupuesto | `02. Planificacion/Presupuesto del Proyecto.xls` | Confirma el gasto real con el equipo (se programó S/ 0) |
| Informe y presentaciones del Sprint 2 | repo | **Sube tus archivos** `informe_sprint2.docx` y `presentacion_sprint2.pptx` |
Además: el nombre del cuarto integrante figura como «Mamani Acuña Frank Joseph» en los documentos y como «Joseph Zevallos Acuña» en Trello; compruébalo con él y corrige el que esté mal.

## 10. Calidad en CRISP-ML(Q) para estas fases
- **Evaluación:** criterios de éxito fijados de antemano (las metas del acta), una sola medición en la prueba, resultados por subgrupo y con y sin imágenes parecidas al entrenamiento, y limitaciones declaradas.
- **Despliegue:** modelos exportados y versionados, preprocesamiento idéntico al entrenamiento, aviso de uso, validación de entradas, plan alternativo y reproducibilidad.
- **Monitoreo y mantenimiento (solo lo básico):** registro de predicciones y confianza, señal simple de deriva y un procedimiento para reentrenar si se detecta (descrito, no ejecutado).
- **Riesgos y mitigación:** ver sección 11.

## 11. Riesgos del Sprint 3
| Riesgo | Mitigación |
|---|---|
| **Falta de tiempo** (hoy es 29 oct) | Respeta las prioridades P0 a P3; recorta P3 primero |
| **Todo recae en ti** | Pide a tus 3 compañeros la revisión, su parte de la exposición y la gestión de equipo; recorta P2 y P3 antes que P0 o P1. Si alguien necesita correr la app, dale los `.onnx` (los `.pt` no hacen falta) |
| **R05: modelo pesado** (U-Net ~100 MB) | ONNX en CPU local; fp16 o Release de GitHub si hace falta |
| **Falla la exportación de la U-Net** | Probar otro `opset_version` y revisar versiones; verificar paridad |
| **Resultado en la prueba peor que en validación** | Es esperable (la prueba difiere del entrenamiento y hay imágenes parecidas): reportar con honestidad, no corregir mirando la prueba |
| **R09: posible atajo por procedencia** | Mostrar resultados por plano y tipo de archivo; declararlo como limitación |
| **Se rompe la demo** | Entorno limpio probado, sin internet, plan alternativo grabado |
| **Alcance del sistema web demasiado grande** | Solo el flujo principal es real; el resto es maqueta |

## 12. Reglas que no se rompen
1. **No inventar datos.** Todo número es medido por el equipo o citado; lo propuesto se llama «propuesta».
2. **La prueba oficial se evalúa una sola vez** (HU12) y no se usa para decidir.
3. **No se cambia la partición** (semilla 42; 3.999 / 1.001 / 1.000).
4. **Solo datos ficticios en la app**; ningún dato de pacientes reales; «apoyo al diagnóstico», no «diagnóstico».
5. **No subir al repo** datos, credenciales ni archivos de más de 100 MB.
6. Mantener el **formato de carpetas** del docente y el **diseño blanco y formal** de documentos y presentaciones.

## 13. Lista final de entrega (antes del 2 de noviembre)
- [ ] Resultados de HU12 con tablas y figuras en el repo.
- [ ] Aplicación con el flujo principal funcionando, README y `requirements-app.txt`.
- [ ] Modelos exportados, `registro_modelos.json` y etiquetas de Git.
- [ ] Informe final en Word y PDF, revisado por los 4.
- [ ] Presentación final con la exposición repartida.
- [ ] Informe y presentación del Sprint 2 en el repo.
- [ ] Trello, Excel, Informe de Estado, Minuta, Riesgos, Retrospectivas y Acta de Cierre al día.
- [ ] **Formato y canal de la entrega final confirmados con el docente** (sección 15.1).
- [ ] README de la raíz del repositorio actualizado (cómo instalar y ejecutar la aplicación).
- [ ] Copia de seguridad de la app y los modelos fuera de tu computadora (sección 15.5).
- [ ] Todo subido a https://github.com/Calamar49/CNN-BRISC.

## 14. Enlaces
Repositorio https://github.com/Calamar49/CNN-BRISC · Trello https://trello.com/b/swXjkoyS/product-backlog-proyecto-redes-neuronales-brisc · BRISC https://www.kaggle.com/datasets/briscdataset/brisc2025/ · artículo https://arxiv.org/abs/2506.14318 y https://www.nature.com/articles/s41597-026-06753-y · plantillas del docente https://github.com/hespetia/gestion-proyectos · ONNX Runtime https://onnxruntime.ai/ · PyTorch https://pytorch.org/get-started/locally/

## 15. Complementos que no debes olvidar
### 15.1 Confirma con el docente (hoy, antes de seguir)
No se sabe y cambia lo que debes preparar:
- **Formato y canal de la entrega final:** ¿enlace al repositorio, archivo comprimido, subida a una plataforma? ¿Qué archivos exactamente (informe, presentación, código, modelos, aplicación)?
- **Duración de la exposición** y si espera **demo en vivo**.
- **Fecha y hora** de la presentación del 30 de octubre.
- **Qué computadora** se usará para presentar (la tuya, la del aula): la demo debe probarse en esa.
- Si acepta el ajuste del «¿para dónde?» del acta (sección 3).

### 15.2 La aplicación: créditos, uso y privacidad
- **Créditos y licencia (obligatorio, CC BY 4.0):** una página «Acerca de» o el pie de la ficha del modelo con la cita de BRISC (Fateh y colaboradores, arXiv 2506.14318 y *Scientific Data*) y el enlace al dataset. Aclara que las imágenes de ejemplo son de ese dataset público.
- **Uso previsto y no previsto** en la ficha del modelo: previsto = demostración académica y apoyo a la lectura del médico; **no previsto** = diagnóstico, uso con pacientes reales, otras secuencias o escáneres.
- **Privacidad:** todo se procesa **en local**, sin enviar imágenes a ningún servicio; **no se guardan las imágenes subidas** ni datos personales en el registro de monitoreo; los pacientes son ficticios. Dilo en la pantalla y en el informe.
- **Inicio de sesión de demostración:** usuarios y contraseñas ficticios, guardados con *hash* (no en texto plano) si usas una base de datos; que no se confunda con seguridad real.

### 15.3 Pruebas mínimas antes de presentar
No hace falta un conjunto grande; bastan tres comprobaciones, guardadas como script para poder repetirlas:
1. **Paridad ONNX frente a PyTorch** (sección 6.2) en 20 imágenes de validación.
2. **Preprocesamiento idéntico:** la imagen que entra a la app produce el mismo tensor que el cargador de entrenamiento (`datos.py`) para 5 imágenes.
3. **Recorrido completo de la aplicación** con las 5 o 6 imágenes de ejemplo y con un archivo inválido, midiendo el tiempo por imagen.

### 15.4 Cómo se ejecuta la demo (que cualquiera la levante)
- Un **script de inicio** (por ejemplo `iniciar_demo.bat` en Windows) que active el entorno y abra la aplicación, y un README con los pasos.
- **Versiones fijadas** (`requirements-app.txt` con `pip freeze`) y la versión de Python con la que probaste. Tu entorno de entrenamiento fue Python 3.12.8, PyTorch 2.11.0 con CUDA 12.8 y una GPU RTX 5060; la aplicación usa solo CPU, así que no debe depender de la GPU.
- Prueba en un **entorno limpio** (otra carpeta, otro usuario o otra computadora) antes de la presentación.

### 15.5 Copia de seguridad
- Haz **commits y `git push` frecuentes** (cada bloque de trabajo terminado), incluso si no está pulido.
- Guarda una **copia de la app, de los modelos exportados (`.onnx`) y de las diapositivas** en un USB y en la nube. El repositorio no contiene los pesos ni los `.onnx` si superan los 100 MB.
- Lleva a la presentación el **video o las capturas** de la demo.

### 15.6 Preguntas probables del docente (y respuestas honestas)
| Pregunta | Respuesta honesta |
|---|---|
| ¿Por qué la precisión es tan alta (~99 %)? | Son cifras de **validación**; en la prueba oficial pueden ser menores. BRISC es un dataset curado, con ~80 % de imágenes con tumor, y hay riesgo de atajo por procedencia (R09) que se midió por plano y tipo de archivo. |
| ¿Se puede usar con pacientes? | No. Es una demostración académica y un apoyo a la lectura, no un diagnóstico; solo conoce T1 con contraste de un dataset público. |
| ¿Qué pasa si el modelo se equivoca? | El médico revisa y decide; el sistema muestra la probabilidad y una alerta de confianza baja; se muestran casos de error en el análisis (HU12). |
| ¿Por qué la U-Net no dice «sin tumor»? | Se entrenó solo con imágenes con máscara; por eso el clasificador decide primero y, si dice «sin tumor», no se muestra máscara. |
| ¿Cómo se evitó la fuga entre entrenamiento y evaluación? | Partición propia con grupos por hash perceptual, prueba oficial intacta y evaluada una sola vez; se reporta aparte el subconjunto sin imágenes parecidas al entrenamiento. |
| ¿Por qué un sistema «para clínicas» si no hay clínica? | Es un prototipo: el flujo de apoyo al diagnóstico es real; los demás módulos son maqueta; no hay datos de pacientes reales. |
| ¿Cómo se reproduce todo? | Con los comandos de los README, la semilla 42, las versiones fijadas y el registro de modelos (HU14). |

### 15.7 Qué decir si HU12 no cumple las metas
Si algún resultado de la prueba queda por debajo de la meta del acta (por ejemplo, el IoU del glioma): **dilo tal cual**, con la causa más probable (contraste bajo del glioma, diferencias entre la prueba y el entrenamiento, imágenes parecidas), sin reentrenar ni cambiar umbrales para corregirlo. Preséntalo como un hallazgo y como trabajo futuro. El acta fija las metas sobre la prueba oficial; la honestidad pesa más que cumplirlas.

### 15.8 Horario sugerido para hoy y mañana [propuesta]
| Bloque | Qué |
|---|---|
| Hoy, bloque 1 (1,5 a 2 h) | Localizar los `.pt`, escribir y ejecutar `evaluar_prueba.py` (HU12) y guardar resultados |
| Hoy, bloque 2 (1 a 1,5 h) | `exportar_onnx.py`, paridad y registro de modelos |
| Hoy, bloque 3 (3 a 4 h) | Flujo principal de la aplicación (pantallas 1 a 8) con datos ficticios e imágenes de ejemplo |
| Hoy, en paralelo | Tus compañeros actualizan las diapositivas con los resultados y ensayan su parte |
| Hoy, cierre (1 h) | Pruebas de la sección 15.3, copia de seguridad, ensayo general |
| 30 oct | Exposición y demo (con plan alternativo a mano) |
| 31 oct | Solo imprevistos |
| 1 a 2 nov | Informe final revisado por los 4, MLOps básico, cierre de gestión y entrega |
Si te atrasas, **no recortes** HU12 ni el flujo principal sin internet; recorta primero la maqueta, la ficha del modelo y el monitoreo.
