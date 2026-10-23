# Traspaso para el Sprint 2 (modelado)

Documento para quien continúe el proyecto y trabaje con su propio Claude. Fecha: **22 de octubre de 2026**.
Lo que está medido o verificado se dice como tal; lo que es **propuesta** o **por confirmar** también.

## 0. Cómo empezar (para tu compañero y su Claude)
1. Clonar el repositorio: `git clone https://github.com/Calamar49/CNN-BRISC.git` y abrir la carpeta con Claude Code (lee `CLAUDE.md` solo).
2. Primer mensaje sugerido a Claude: *«Lee CLAUDE.md y docs/TRASPASO_SPRINT2.md. Revisa el estado del repositorio y dime qué falta para HU05. No inventes datos y pregúntame lo que no esté claro.»*
3. Preparar el entorno (sección 7) y los datos (sección 4).
4. Confirmar con el equipo, **antes de entrenar**, qué se hizo del Sprint 2 fuera del repositorio (en el repositorio no hay código de entrenamiento) y quién hace qué.

## 1. El proyecto en una página
- **Qué es:** un sistema que, dada una resonancia magnética cerebral (T1 con contraste), **clasifica** el tipo de tumor (glioma, meningioma, tumor de hipófisis o sin tumor) y **segmenta** su contorno; se mostrará en una aplicación web de demostración académica.
- **Quién:** 4 estudiantes (Coavoy Cruz Joseph Gabriel, gerente; Cuchuyrrumi Mamani Manuel Rodrigo, Scrum Master; Huallpatuiro Rafaile Brayan y Mamani Acuña Frank Joseph, desarrollo). Docente revisor: Ing. Hugo Espetia Huamanga. No hay patrocinador ni Dueño del Producto.
- **Metodología:** Scrum + CRISP-ML(Q). Sprint 1 = negocio y datos (+ preparación); Sprint 2 = modelado; Sprint 3 = evaluación y despliegue.
- **Fechas:** Sprint 2, 10–22 oct (presentación **23 oct**); Sprint 3, 24–29 oct (presentación final **30 oct**); margen 31 oct; **entrega límite 2 nov 2026**.
- **Metas del acta** (propuestas del equipo, aún no evaluadas; sobre la prueba oficial): accuracy ≥ 95 %, recall ≥ 90 % por clase, IoU ≥ 70 %.
- **Referencia del artículo de BRISC** (resultados de los autores, no nuestros; vienen de la versión preliminar y hay que cotejarlos con la publicada en *Scientific Data*): EfficientNetB0 99,2 % y ResNet50 98,2 % de accuracy; Xception, DenseNet y MobileNetV2 rindieron mal o de forma inestable; U-Net con mIoU ponderado de 75,7 %.

## 2. Estado al 22 de octubre de 2026
| Parte | Estado |
|---|---|
| HU01 a HU04 (Sprint 1) | Terminadas. Acta firmada. En Trello, HU01–HU03 están en «Terminado»; en HU04 faltan por marcar la retroalimentación del docente y la revisión del backlog del Sprint 2. |
| Datos | Descargados, analizados, preparados y verificados (sección 4). |
| HU05–HU09 (Sprint 2) | **Sin código en el repositorio.** En Trello, HU05 está en «En progreso» (desde el 16 oct) y HU06–HU17 siguen en «Product Backlog». Confirmar con el equipo. |
| Entrenamiento de modelos | No hay ningún modelo entrenado ni métrica de desempeño en el repositorio. |
| Informe y presentaciones del Sprint 1 | Hechos (`03. Implementacion/Informe del Sprint 1.pdf`/`.docx`, `04. Revision y retrospectiva/Revisión del Sprint.pptx`). La Retrospectiva tiene los campos por llenar. |
| Retraso | Si no hay resultados de modelos para el 23 de octubre, véase el plan de tiempo (sección 10). |

### Actualización — 23 de octubre de 2026 (técnico, hecho con Claude Code en una sesión de trabajo)

HU05 a HU09 ya tienen código y resultados reales en el repositorio, en `03. Implementacion/Sprint 2 - Entrenamiento/`:

| Parte | Estado |
|---|---|
| HU05 | Hecho: 2 arquitecturas de clasificación con transfer learning (EfficientNetB0, ResNet50) y U-Net definida para segmentación, ambas entrenadas con métrica registrada. |
| HU06 | Hecho: EfficientNetB0 elegida, 99,52 % de recall medio en validación (modelo base); curvas y mejor checkpoint guardados. |
| HU07 | Hecho: U-Net (encoder ResNet34) entrenada solo con imágenes con máscara, 79,70 % de IoU en validación (modelo base); ejemplos de máscara predicha guardados. |
| HU08 | Hecho: 3 configuraciones extra probadas por tarea (lr, batch, sin aumento) frente al modelo base; ganadoras `batch=64` (clasificador) y `lr=1e-4` (U-Net); entrenamiento final repetido con 2 semillas más (promedios: 99,57 % ± 0,12 % recall medio; 80,12 % ± 0,27 % IoU). |
| HU09 | Hecho: 13 entrenamientos registrados en `experimentos.csv` con configuración, métricas y tiempo; tabla completa incluida en `herramientas/informe_sprint2.docx`. |
| Riesgo R09 | Investigado con datos reales (`evaluar_grupos.py`): sin diferencias relevantes por plano de corte; el glioma es la clase más difícil de segmentar (67,43 % IoU) y hay una brecha gris/RGB de ~8 puntos en la U-Net, probablemente explicada por la dificultad propia del glioma más que por un atajo puro — detalle en el README de `Sprint 2 - Entrenamiento/` y en el informe. |
| **Lo que sigue faltando (no técnico, a cargo del equipo)** | Backlog del Sprint 2 en Trello/Excel, Informe de Estado, Minuta, Registro de Riesgos (agregar R09), Retrospectiva del Sprint 2 y la presentación del Sprint 2 (HU10, 23 oct) — ver sección 15.1. |

## 3. Lo que se hizo en el Sprint 1 (resumen; detalle en el informe)
**Etapa 1 · Comprensión del negocio (HU01).** Acta de Constitución firmada, Product Backlog de 17 historias en Trello (criterios de aceptación, puntos, dependencias, fase CRISP-ML(Q)), Gantt y CSV, plantillas de gestión llenas, datos públicos del problema (GLOBOCAN, Minsa, SuSalud), objetivos, metas y factibilidad. Presupuesto programado: S/ 0.

**Etapa 2 · Comprensión de los datos (HU02).** Notebook `01_HU02_EDA_BRISC.ipynb` y script `perfil_datos.py` (resultados en `salida_sprint1/`, ignorada por Git: se regenera). Resultados medidos:
- 6.000 imágenes (5.000 entrenamiento y 1.000 prueba); conteos por clase y partición iguales a los del artículo; 4.793 pares imagen–máscara; las 1.207 imágenes sin tumor **no tienen máscara**.
- Máscaras con valores intermedios (0 a 6 y algunos 250); 183 combinaciones de tamaño (512×512 en 4.881 imágenes); 2.866 imágenes en gris y 3.134 en RGB con canales iguales.
- Tumor: 0,9 % (hipófisis) a 1,7 % (meningioma) de la imagen en mediana; 8,3 % de las máscaras con más de una región; contraste mediano tumor/tejido: glioma 1,07, meningioma 1,52, hipófisis 1,45; hipófisis muy centrada.
- 96 archivos con SHA-256 repetido (7 entre entrenamiento y prueba). Licencia CC BY 4.0.
- Brillo y encuadre cambian con la clase (posible atajo, riesgo R09 propuesto) y la prueba oficial difiere moderadamente del entrenamiento.

**Etapa 3 · Preparación de los datos (HU03).** Notebook `02_HU03_particion_y_cargador.ipynb`.
- Integridad: 0 archivos corruptos, 0 máscaras sin imagen o vacías.
- Hash perceptual (dHash de 256 bits, umbral 16, elegido midiendo distancias; el primer intento con 64 bits y umbral 6 formaba un grupo de 1.933 imágenes distintas): 4.938 grupos en el entrenamiento oficial, el mayor de 3.
- **Partición propia (semilla 42):** 3.999 entrenamiento / 1.001 validación (20 %, por clase y plano, sin partir grupos) / 1.000 prueba oficial intacta.
- Preprocesamiento fijado: relleno a cuadrado sin deformar, 256×256, interpolación bilineal (imágenes) y *nearest* (máscaras), máscaras binarizadas > 127, normalización de ImageNet (media 0,485 0,456 0,406; desvío 0,229 0,224 0,225).
- 113 a 123 de las 1.000 imágenes de prueba tienen un vecino casi idéntico en entrenamiento (informativo).
- Cargador probado con un lote real; ejecución reproducible (en un entorno limpio, los CSV de partición salieron idénticos byte a byte).

**Después del sprint:** dataset ya preparado en `~/datasets/brisc2025_preparado` (script `preparar_dataset.py`, verificado con `verificar_preparado.py`), informe de 27 páginas, presentación de 29 diapositivas con reparto de exposición, scripts generadores en `herramientas/`.

## 4. Datos: dónde están y cómo regenerarlos
Todo en la carpeta `03. Implementacion/Sprint 1 - Notebooks/` (después de `pip install -r requirements-probado.txt`):
```bash
python descargar_brisc.py        # baja BRISC a ~/datasets/brisc2025 (~280 MB; no requiere iniciar sesión en Kaggle)
python ejecutar_sprint1.py       # corre los dos notebooks; crea salida_sprint1/ (incluye la partición)
python preparar_dataset.py       # crea ~/datasets/brisc2025_preparado (6.000 imágenes y 4.793 máscaras)
python verificar_preparado.py    # debe terminar con «RESULTADO: todo correcto»
python perfil_datos.py           # opcional (~4 min): perfil de intensidad, ubicación y contraste
```
**Dataset preparado** (`~/datasets/brisc2025_preparado`):
```
imagenes/{train,val,test}/{glioma,meningioma,pituitary,no_tumor}/*.png   256×256, un canal
mascaras/{train,val,test}/{glioma,meningioma,pituitary}/*.png            256×256, valores 0 y 255
manifest_preparado.csv    archivo, particion, clase, plano, grupo_hash, tiene_mascara, ruta_imagen, ruta_mascara,
                          particion_oficial, duplicado_exacto, sha256_original, ancho_original, alto_original, area_tumor_original
```
Conteos: glioma 917 / 230 / 254; meningioma 1.063 / 266 / 306; hipófisis 1.166 / 291 / 300; sin tumor 853 / 214 / 140 (entrenamiento / validación / prueba). Máscaras: 3.146 / 787 / 860.
La normalización de ImageNet **no** está guardada: se aplica al cargar (el README de esa carpeta trae un ejemplo).
Para saber si una imagen era gris o RGB en origen: columna `mode` de `salida_sprint1/perfil_datos/perfil_imagenes.csv` (se une por nombre de archivo).

## 5. Qué hay que hacer en el Sprint 2 (backlog)
Fechas del Gantt entre paréntesis; puntos y dependencias del Product Backlog en Trello.
| HU | Qué | Fechas | Puntos | Depende de |
|---|---|---|---|---|
| HU05 | Seleccionar arquitectura y entrenar el modelo base | 12–13 oct | 3 | HU03 |
| HU06 | Entrenar el clasificador de tipo de tumor (4 clases) | 14–18 oct | 8 | HU05 |
| HU07 | Entrenar el modelo de segmentación U-Net | 14–18 oct | 8 | HU05 |
| HU08 | Ajustar hiperparámetros y mejorar los modelos (aumento de datos) | 19–21 oct | 5 | HU06, HU07 |
| HU09 | Registrar y comparar experimentos | 21–22 oct | 3 | HU08 |
| HU10 | Presentación del Sprint 2 | 23 oct | 2 | HU09 |
| HU11 | (Opcional) Modelo multitarea con encoder compartido | solo si hay tiempo | 8 | HU09 |

**Criterios de aceptación que figuran en Trello** (revisados el 22 de octubre; ninguno está marcado todavía):
- **HU05:** al menos 2 arquitecturas de clasificación candidatas con transfer learning, justificadas · arquitectura U-Net definida para la segmentación · modelo base entrenado y su métrica registrada.
- **HU06:** curvas de entrenamiento y validación guardadas · accuracy y recall por clase en validación reportados · mejor modelo guardado junto con su configuración.
- **HU07:** entrenamiento solo con imágenes que tienen máscara · IoU en validación reportado (referencia del artículo: U-Net 75,7 %) · ejemplos de máscara predicha frente a la real.
  *Aclaración:* las 4.793 imágenes con máscara están repartidas en entrenamiento (3.146), validación (787) y prueba (860); entrenar solo con las 3.146 de entrenamiento.
- **HU08:** al menos 3 configuraciones probadas (tasa de aprendizaje, aumento de datos, tamaño de lote u otras) · mejora medida frente al modelo base · la prueba oficial no se usa para decidir qué configuración elegir.
- **HU09:** tabla con parámetros, métricas y tiempo de entrenamiento de cada experimento · modelo(s) elegido(s) con su justificación · tabla incluida en el informe final.
- **HU10 a HU17:** no se revisaron sus checklists; verlos en el tablero.

**Estado de las tarjetas en Trello (22 de octubre):** HU01–HU03 en «Terminado» (con fecha cumplida y miembros asignados); HU04 sigue en la lista «Sprint 1» sin marcar (faltan la retroalimentación del docente y la revisión del backlog del Sprint 2); **HU05 en «En progreso» desde el 16 de octubre**; **HU06 a HU17 siguen en «Product Backlog»** y la lista «Sprint 2 (10-22 oct)» está vacía, es decir, la planificación del Sprint 2 no está reflejada en el tablero. Ninguna de HU05–HU11 tiene miembros, comentarios ni criterios marcados. **Las fechas de entrega de HU05 a HU09 vencen el 22 de octubre (hoy)** y la de HU10 el 23.

## 6. Cómo lo haremos (propuesta técnica; confirmar con el equipo)
### 6.1 Clasificador (HU05, HU06, HU08)
- **Entrada:** 3×256×256 (imagen en gris repetida en 3 canales, normalización de ImageNet). Salida: 4 clases.
- **Arquitecturas candidatas:** EfficientNetB0 y ResNet50 con pesos de ImageNet (transfer learning), cambiando la última capa a 4 salidas. Son las que mejor rindieron en el artículo; Xception, DenseNet y MobileNetV2 se reportaron inestables.
- **Pérdida:** entropía cruzada (con pesos por clase opcionales; el desbalance es moderado, de 1.207 a 1.757 imágenes por clase).
- **Optimización, punto de partida a ajustar:** AdamW, tasa de aprendizaje 3e-4 con *cosine*, 15 a 30 épocas, parada temprana por recall medio en validación (paciencia 5), precisión mixta (`torch.autocast`).
- **Aumento de datos (moderado):** rotación hasta ±10°, escala 0,9–1,1, brillo y contraste ±20 %, giro horizontal. **Evitar desplazamientos grandes:** el tumor de hipófisis está muy centrado y la posición es una pista.
- **Mitigación del posible atajo (R09):** normalizar la intensidad de cada imagen y aumentar brillo y contraste; **reportar siempre** las métricas por plano de corte y por tipo de archivo (gris o RGB).
- **Métricas:** accuracy, recall por clase, F1 macro, matriz de confusión. Repetir el entrenamiento final con 2 o 3 semillas y reportar el promedio.

### 6.2 Segmentación (HU05, HU07, HU08)
- **Datos:** solo imágenes con máscara (3.146 entrenamiento y 787 validación). **Sin tumor no tiene máscara:** no entra en la segmentación.
- **Modelo:** U-Net con codificador preentrenado (por ejemplo ResNet34). Opción rápida: `segmentation-models-pytorch`; si no instala con Python 3.13, escribir la U-Net con un codificador de `torchvision`.
- **Pérdida:** BCE + Dice (o focal), porque el tumor es el 0,9–1,7 % de la imagen en mediana. Umbral de salida 0,5.
- **Métricas:** IoU y Dice sobre imágenes con tumor, también por clase. Se espera que el glioma sea la clase más difícil (contraste casi igual al tejido). El 8,3 % de las máscaras tiene varias regiones: el modelo debe poder marcar más de una.
- **Aumento:** el mismo en imagen y máscara a la vez (por ejemplo `torchvision.transforms.v2`, que transforma ambas con la misma transformación; la máscara con *nearest*).

### 6.3 Modelo multitarea (HU11, opcional)
Un codificador compartido con una cabeza de clasificación y un decodificador de segmentación; pérdida total = clasificación + λ · segmentación, **ignorando la pérdida de segmentación en las imágenes sin tumor**. Solo si HU05–HU09 están cerradas; se compara con los dos modelos separados.

### 6.4 Protocolo de evaluación
- Elegir arquitectura, hiperparámetros y época **solo con validación**. La **prueba oficial no se usa** hasta HU12 (Sprint 3), una sola vez.
- Opcional al final: reentrenar con entrenamiento + validación (5.000 imágenes) con el número de épocas fijado en validación, y evaluar una vez en la prueba. Informar que parte de la prueba se parece al entrenamiento (113–123 imágenes).
- Reportar resultados por clase, por plano y por tipo de archivo, no solo el promedio.

### 6.5 Registro de experimentos (HU09)
Un archivo `experimentos.csv` con **una fila por entrenamiento**, además de guardar la configuración (JSON), la curva de entrenamiento y el punto de control en `salida_sprint2/` (ignorada por Git):
`id, fecha, historia, tarea (clasificacion/segmentacion), arquitectura, preentrenado, tamano_imagen, batch, lr, optimizador, perdida, epocas, epoca_optima, aumento, semilla, val_accuracy, val_recall_por_clase, val_f1_macro, val_iou, val_dice, tiempo_min, checkpoint, notas`.

### 6.6 Estructura de código sugerida
```
03. Implementacion/Sprint 2 - Entrenamiento/
├─ datos.py                  Dataset de PyTorch que lee manifest_preparado.csv (aplicar normalización al cargar)
├─ modelos.py                clasificador (EfficientNetB0 / ResNet50) y U-Net
├─ metricas.py               accuracy, recall por clase, F1, IoU, Dice
├─ entrenar_clasificador.py  argumentos: arquitectura, lr, épocas, semilla ... → escribe una fila en experimentos.csv
├─ entrenar_unet.py
├─ experimentos.csv
└─ salida_sprint2/           puntos de control, curvas y figuras (no se sube a Git)
```
Ejemplo mínimo de carga con el manifest (el resto del cargador está probado en el notebook `02_HU03`):
```python
import numpy as np, pandas as pd
from PIL import Image
from torch.utils.data import Dataset

MEDIA = np.array([0.485, 0.456, 0.406], dtype=np.float32)[:, None, None]
DESVIO = np.array([0.229, 0.224, 0.225], dtype=np.float32)[:, None, None]
CLASES = ["glioma", "meningioma", "pituitary", "no_tumor"]

class Brisc(Dataset):
    def __init__(self, raiz, particion):
        m = pd.read_csv(f"{raiz}/manifest_preparado.csv")
        self.t, self.raiz = m[m.particion == particion].reset_index(drop=True), raiz
    def __len__(self): return len(self.t)
    def __getitem__(self, i):
        r = self.t.iloc[i]
        x = np.asarray(Image.open(f"{self.raiz}/{r.ruta_imagen}"), dtype=np.float32) / 255.0
        x = (np.stack([x] * 3) - MEDIA) / DESVIO
        if r.tiene_mascara:
            m = (np.asarray(Image.open(f"{self.raiz}/{r.ruta_mascara}")) > 127).astype(np.float32)[None]
        else:
            m = np.zeros((1, 256, 256), dtype=np.float32)
        return x, CLASES.index(r.clase), m, bool(r.tiene_mascara)
```

## 7. Con qué lo haremos (entorno y versiones)
**Equipo de referencia** (donde se hizo el Sprint 1): Windows 11, Python **3.13.14**, GPU **NVIDIA GeForce RTX 4050 Laptop de 6 GB** (controlador 610.78).
**Versiones usadas en el Sprint 1** (`requirements-probado.txt`): numpy 2.5.1, pandas 3.0.5, matplotlib 3.11.1, pillow 12.3.0, scikit-learn 1.9.0, nbconvert 7.17.1, nbformat 5.11.1, ipykernel 7.3.0, kaggle 2.2.4. También instalados en ese equipo: scipy 1.18.0, onnx 1.23.2, onnxruntime 1.31.0.

**Problema importante:** el PyTorch instalado en ese equipo (**2.13.0**) es **solo CPU** (`torch.cuda.is_available()` da `False`), y `torchvision` no está instalado. Para entrenar con la GPU hay que instalar la versión con CUDA:
```bash
python -m pip uninstall -y torch
# Elegir el comando exacto en https://pytorch.org/get-started/locally/  (Stable, Windows, Pip, la versión de CUDA que corresponda al controlador)
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/<cuXXX>     # <cuXXX> lo indica la página
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"                    # debe imprimir True
```
Con la GPU de 6 GB, puntos de partida a **verificar con `nvidia-smi`**: clasificador a 256 px con lote 32 y precisión mixta; U-Net a 256 px con lote 8 a 16 y precisión mixta. Si falta memoria, bajar el lote o la resolución (224) antes de cambiar de modelo. Colab gratuito queda como respaldo.

**Librerías nuevas para el Sprint 2** (instalar las versiones estables actuales y luego fijarlas en `requirements-sprint2.txt` con `pip freeze`): `torchvision` (obligatoria), `segmentation-models-pytorch` y `timm` (opcionales, para la U-Net con codificador preentrenado), `tensorboard` (opcional). Para exportar a la aplicación web (Sprint 3): `onnx` y `onnxruntime` (ya instalados); el tamaño del modelo en el navegador es el riesgo R05.

## 8. Qué se necesita antes de empezar (lista de comprobación)
- [ ] Acceso al repositorio (si es privado, el dueño debe invitar al compañero) y `git` configurado.
- [ ] Python 3.13 (o el que use el equipo; fijar la versión en el README) y `pip install -r requirements-probado.txt`.
- [ ] GPU con CUDA funcionando (`torch.cuda.is_available() == True`) o Colab como respaldo.
- [ ] Dataset descargado y preparado, con `verificar_preparado.py` en «todo correcto».
- [ ] Acceso al tablero de Trello (también el docente lo necesita para abrir el enlace).
- [ ] Acordar quién hace HU06 (clasificador) y quién HU07 (U-Net): son independientes y se pueden hacer en paralelo.
- [ ] Decidir el framework y el formato de exportación del modelo (**propuesta:** PyTorch y ONNX).

## 9. Riesgos y cuidados
| Riesgo | Qué hacer |
|---|---|
| R01 Fuga entre pacientes (sin ID de paciente) | Usar solo la partición propia; agrupar por `grupo_hash`; reportar con la prueba oficial y avisar de las 113–123 imágenes parecidas. |
| R09 (propuesto) Atajos por procedencia de la imagen | Normalizar intensidad, aumentar brillo/contraste y reportar por plano y tipo de archivo. Falta agregarlo al Registro de Riesgos. |
| R04 Arquitecturas inestables | Partir de EfficientNetB0 / ResNet50 y repetir con 2–3 semillas. |
| R06 Memoria de GPU de 6 GB o sobreajuste | Precisión mixta, lote pequeño, parada temprana; Colab de respaldo. |
| R05 Modelo pesado para el navegador | Preferir modelos livianos o cuantizados (ONNX) y decidirlo en el Sprint 3. |
| R07 Retraso del cronograma | Ver el plan de tiempo (sección 10). |
| Usar la prueba para decidir | No. Se evalúa una sola vez en HU12. |
| Subir pesos o datos a Git | No: GitHub rechaza archivos de más de 100 MB; los pesos están ignorados en `.gitignore`. |

## 10. Plan de tiempo (22 de octubre → 2 de noviembre de 2026)
- **22 oct (hoy):** confirmar el estado real del Sprint 2, preparar el entorno con GPU, escribir `datos.py`, `modelos.py` y `metricas.py`.
- **Para la presentación del 23 oct (HU10):** lo realista es mostrar el **pipeline de entrenamiento funcionando** y los **resultados parciales de validación** del clasificador base y de la U-Net base, con el registro de experimentos iniciado. Si todavía no hay modelos, decirlo con claridad y mostrar el plan; **no presentar cifras del artículo como propias**.
- **24–25 oct:** cerrar HU06 y HU07 y empezar HU08 (aumento de datos, tasa de aprendizaje) y HU09 (tabla de experimentos).
- **26–29 oct (Sprint 3):** HU12 evaluación única en la prueba oficial; HU13 aplicación web con el modelo exportado; HU14 MLOps básico (versionado y registro de métricas); HU15 informe final; HU16 exposición y ensayo.
- **30 oct** presentación final · **31 oct** margen · **2 nov** fecha límite.
Si el tiempo no alcanza, **recortar primero** HU11 (multitarea, opcional) y la reentrenada final con 5.000 imágenes.

## 11. Pendientes heredados del Sprint 1
- **Excel:** las hojas «Sprints» de `Backlog del Producto.xlsx` y `Backlog Detallado del Producto.xlsx` conservan las fechas de la plantilla (2018); la hoja «Sprint 2» de `Backlog del Sprint.xlsx` conserva ejemplos de la plantilla (Luis, Jorge, Carolina, Lucía); `Registro de Impedimentos.xlsx` solo tiene el encabezado.
- **Registro de Riesgos:** agregar el R09 propuesto.
- **Trello:** en HU04, marcar la retroalimentación del docente y la revisión del backlog del Sprint 2; comentarios de HU02 y HU03 dicen «pendiente de revisión»; mover HU06 a HU11 a la lista «Sprint 2», asignar responsables y revisar los criterios de HU10 a HU17. En Trello aparece como miembro «Joseph Zevallos Acuña» y el equipo de los documentos tiene a «Mamani Acuña Frank Joseph»: comprobar que los nombres coincidan.
- **Retrospectiva del Sprint:** llenar los campos con el equipo (el resto de la presentación está hecho).
- **Informe de Estado y Minuta:** campos del equipo por llenar (fecha y lugar de la reunión, gastos registrados).
- **Informe del Sprint 1:** las secciones 2.3 y 2.4 aún incluyen los grupos hipotéticos, el escenario de clínica con supuestos y el ejemplo de prevalencia (se quitaron de las diapositivas).
- **Cronograma detallado (.mpp)** sin llenar; imagen del Gantt del acta con fechas anteriores.
- **Cotejar** las cifras de referencia del artículo (versión preliminar de arXiv) con la versión publicada en *Scientific Data*.

## 12. Herramientas incluidas
`herramientas/` tiene los generadores del informe (`build_informe.py`), de las presentaciones (`deck_light.py`) y de los gráficos (`gen_figs.py`). Ver `herramientas/README.md`.

## 13. Enlaces
- Repositorio: https://github.com/Calamar49/CNN-BRISC
- Trello: https://trello.com/b/swXjkoyS/product-backlog-proyecto-redes-neuronales-brisc
- Dataset (Kaggle): https://www.kaggle.com/datasets/briscdataset/brisc2025/ · copia en Mendeley: https://data.mendeley.com/datasets/c7dj4pwhcv
- Artículo (arXiv): https://arxiv.org/abs/2506.14318 · versión en revista: https://www.nature.com/articles/s41597-026-06753-y
- Plantillas del docente: https://github.com/hespetia/gestion-proyectos
- PyTorch (instalación): https://pytorch.org/get-started/locally/

## 14. Glosario mínimo
- **HU:** historia de usuario. **EDA:** análisis exploratorio de datos. **CRISP-ML(Q):** ciclo de vida de un proyecto de aprendizaje automático con calidad.
- **Clasificación:** decir qué tipo de tumor hay. **Segmentación:** marcar en qué píxeles está.
- **IoU / Dice:** cuánto se solapa la máscara predicha con la real. **Recall:** de los casos reales de una clase, cuántos detecta el modelo.
- **Transfer learning:** partir de una red entrenada con otro dataset (ImageNet). **Fuga:** que imágenes casi iguales caigan en entrenamiento y en evaluación, inflando los resultados.

## 15. Entregables de gestión del Sprint 2 (Scrum) y calidad en la fase de modelado (CRISP-ML(Q))
El Sprint 2 no son solo modelos: en Scrum cada sprint deja evidencia de gestión, y en CRISP-ML(Q) cada fase incluye un paso de calidad.

### 15.1 Qué hay que dejar al cierre del Sprint 2 (propuesta, siguiendo lo hecho en el Sprint 1)
| Entregable | Dónde | Qué hacer |
|---|---|---|
| Backlog del Sprint 2 | `02. Planificacion/Backlog del Sprint.xlsx`, hoja «Sprint 2» | Hoy tiene ejemplos de la plantilla: reemplazarlos por las tareas reales de HU05 a HU09, con responsable, estado y horas estimadas (propuesta del equipo). Corregir también las hojas «Sprints» de los dos backlogs (fechas de 2018). |
| Tablero de Trello | enlace en la sección 13 | Mover las tarjetas HU05–HU09 a «En progreso» y «Terminado» según avancen; marcar los criterios de aceptación **solo cuando estén cumplidos y revisados por otra persona** (definición de terminado propuesta en la tarjeta de metodología). Dejar comentarios con resultados, como se hizo en HU02 y HU03. |
| Informe de Estado del Proyecto | `03. Implementacion/Informe de Estado del Proyecto.docx` | Actualizar el periodo, el avance (historias terminadas de 17) y los riesgos. |
| Minuta de Reunión | `03. Implementacion/Minuta de Reunión.docx` | Registrar la planificación y la revisión del Sprint 2 con fecha, lugar y acuerdos reales del equipo. |
| Registro de Riesgos e Impedimentos | `02. Planificacion/Registro de Riesgos.xls`, `03. Implementacion/Registro de Impedimentos.xlsx` | Agregar R09 y los riesgos nuevos; anotar cada impedimento real (por ejemplo, falta de GPU o de tiempo). |
| Revisión del Sprint 2 (HU10, 23 oct) | `04. Revision y retrospectiva/` | Presentación con el mismo diseño blanco del Sprint 1: copiar y adaptar `herramientas/deck_light.py`. Estructura sugerida: meta del sprint, qué se hizo por historia, resultados en validación, tabla de experimentos, decisiones, riesgos y plan del Sprint 3. Repartir la exposición en bloques seguidos y equitativos. |
| Retrospectiva del Sprint 2 | misma carpeta | Hacerla **con el equipo**; no escribir respuestas por ellos. |
| Código y resultados | `03. Implementacion/Sprint 2 - Entrenamiento/` | Con README que explique cómo reproducir (comandos, semilla, versiones). |
| Cronograma | `02. Planificacion/` | Actualizar el avance (columna Progress) del CSV del Gantt. |

### 15.2 Calidad en CRISP-ML(Q) para la fase de modelado
En CRISP-ML(Q), cada fase pide definir requisitos y restricciones, identificar riesgos y mitigarlos, y documentarlo. Para el modelado, en este proyecto eso significa:
- **Requisitos:** las metas del acta (accuracy ≥ 95 %, recall ≥ 90 % por clase, IoU ≥ 70 %) y las restricciones (GPU de 6 GB, plazos, solo T1 con contraste).
- **Riesgos y mitigación:** los de la sección 9 (fuga, atajos R09, memoria de GPU, arquitecturas inestables).
- **Selección de modelos documentada:** cada intento queda en `experimentos.csv` y la elección se justifica con datos de validación.
- **Reproducibilidad:** semilla fija, configuración guardada, versiones de las librerías y comandos en el README.
- **Robustez:** resultados por clase, por plano y por tipo de archivo, con 2 o 3 semillas para ver la variabilidad.
- **Sin fuga hacia la evaluación:** la prueba oficial no se usa hasta HU12.
- **Honestidad:** distinguir siempre lo medido por el equipo de lo que viene del artículo, y lo propuesto de lo confirmado.

### 15.3 Lo que este traspaso no puede resolver
- **No hay garantía de que el Sprint 2 salga completo:** depende del tiempo (quedan días contados), de la GPU y del trabajo del equipo. El documento da el plan y el contexto, no los resultados.
- **El criterio del equipo y del docente:** las decisiones marcadas como propuesta (arquitecturas, hiperparámetros, estructura) hay que confirmarlas con el equipo; si el docente pide otra cosa, prevalece.
- **Lo que está solo en Trello o en conversaciones** (por ejemplo, los criterios de HU05 a HU17 y cualquier acuerdo verbal) no está en este repositorio: revisarlo en el tablero.
