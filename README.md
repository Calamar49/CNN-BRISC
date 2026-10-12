# Sistema Inteligente para clasificar y segmentar tumores cerebrales en resonancias magnéticas

> Desarrollo de un Sistema Inteligente para clasificar y segmentar tumores cerebrales en resonancias magnéticas (**¿para qué?**), desplegado en una aplicación web de apoyo académico (**¿para dónde?**).

Proyecto académico de Redes Neuronales – Opción B (Ingeniería de Sistemas, Inteligencia Artificial). Docente revisor: Ing. Hugo Espetia Huamanga.
Es una demostración académica: **no es una herramienta de diagnóstico médico**.

## Equipo
| Integrante | Rol (propuesta) |
|---|---|
| Coavoy Cruz Joseph Gabriel | Gerente de Proyecto |
| Cuchuyrrumi Mamani Manuel Rodrigo | Scrum Master |
| Huallpatuiro Rafaile Brayan | Equipo de desarrollo |
| Mamani Acuña Frank Joseph | Equipo de desarrollo |

No hay patrocinador ni Dueño del Producto: el equipo define y prioriza el backlog.

## Enlaces
- Product Backlog (Trello, tablero privado): https://trello.com/b/swXjkoyS/product-backlog-proyecto-redes-neuronales-brisc
- Dataset BRISC 2025 (Kaggle): https://www.kaggle.com/datasets/briscdataset/brisc2025/ (licencia CC BY 4.0 según los metadatos de Kaggle; hay que citar a los autores)
- Artículo del dataset: https://arxiv.org/abs/2506.14318

## Metodología híbrida: Scrum + CRISP-ML(Q)
Scrum organiza el trabajo (backlog, sprints, presentación al docente y retrospectiva) y CRISP-ML(Q) organiza el ciclo de vida del modelo.

| Sprint | Trabajo | Presentación | Fase CRISP-ML(Q) |
|---|---|---|---|
| 1 | 1 – 8 oct 2026 | lun 12 oct | Comprensión del negocio y de los datos + preparación de los datos |
| 2 | 10 – 22 oct 2026 | vie 23 oct | Modelado |
| 3 | 24 – 29 oct 2026 | vie 30 oct | Evaluación y despliegue (MLOps básico) |

Margen de seguridad: 31 oct. Fecha límite del docente: lun 2 nov 2026.

## Estructura de carpetas (formato del repositorio del docente)
Se mantiene la estructura numerada y los nombres de archivo de la plantilla `hespetia/gestion-proyectos`.

| Carpeta | Contenido | Estado |
|---|---|---|
| `01. Inicio` | Acta de Constitución, Backlog del Producto, Registro de Interesados, Planificación de Lanzamiento | Lleno |
| `02. Planificacion` | Backlog Detallado, Backlog del Sprint (hoja Sprint 1), Cronograma de alto nivel – Hitos, Presupuesto, Registro de Riesgos, CSV del Gantt | Lleno (Cronograma detallado `.mpp` sin llenar) |
| `03. Implementacion` | Informe de Estado, Minuta de Reunión, Registro de Impedimentos, `Sprint 1 - Notebooks/` | Borradores con campos `[completar]` |
| `04. Revision y retrospectiva` | Revisión del Sprint y Retrospectiva del Sprint (Sprint 1) | Borrador |
| `05. Lanzamiento`, `06. Cierre` | Plantillas sin llenar (se usan al final del proyecto) | Pendiente |

## Notebooks del Sprint 1
En `03. Implementacion/Sprint 1 - Notebooks/`:
- `01_HU02_EDA_BRISC.ipynb`: análisis exploratorio del dataset.
- `02_HU03_particion_y_cargador.ipynb`: verificación, partición sin fuga evidente y cargador de datos.

Se ejecutan **en local** (sin Kaggle Notebooks). El informe completo del sprint está en `03. Implementacion/Informe del Sprint 1.pdf`.

## Cómo reproducir los resultados del Sprint 1

**Requisitos:** Python 3.11 o superior (se verificó con 3.13.14 en Windows 11), unos 300 MB libres para el dataset y conexión a internet. No hace falta GPU ni PyTorch en el Sprint 1.

```bash
git clone https://github.com/Calamar49/CNN-BRISC.git
cd CNN-BRISC
pip install -r requirements-probado.txt      # versiones exactas con las que se verificó (o requirements.txt, sin fijar versiones)
cd "03. Implementacion/Sprint 1 - Notebooks"
python descargar_brisc.py                    # baja BRISC 2025 a ~/datasets/brisc2025 (fuera de OneDrive); no requiere iniciar sesión en Kaggle
python ejecutar_sprint1.py                   # corre los dos notebooks (unos minutos) y escribe salida_sprint1/
```
Alternativa: abrir los notebooks en VS Code (extensión Jupyter) y usar **Run All**, en este orden: `01_HU02_EDA_BRISC.ipynb` y `02_HU03_particion_y_cargador.ipynb`. Si el dataset ya está en otra carpeta, define la variable de entorno `BRISC_ROOT` con esa ruta.

**Qué debes obtener** (si algo no coincide, revisa el notebook ejecutado en `salida_sprint1/notebooks_ejecutados/`):

| Comprobación | Valor esperado |
|---|---|
| Imágenes de clasificación | 6.000 (5.000 entrenamiento y 1.000 prueba) |
| Por clase (entrenamiento / prueba) | glioma 1.147 / 254 · meningioma 1.329 / 306 · hipófisis 1.457 / 300 · sin tumor 1.067 / 140 |
| Pares imagen–máscara | 4.793 (las 1.207 imágenes sin tumor no tienen máscara) |
| Combinaciones de tamaño de imagen | 183 (la más frecuente, 512×512 con 4.881) |
| Duplicados exactos (SHA-256) en clasificación | 96 archivos; 7 hashes repartidos entre entrenamiento y prueba |
| Grupos de imágenes casi idénticas (umbral 16) | 4.938 grupos en el entrenamiento oficial; el mayor, de 3 |
| Imágenes de prueba con vecino casi idéntico en entrenamiento | 113 (dHash) y 123 (correlación) de 1.000 |
| Partición propia | 3.999 entrenamiento / 1.001 validación / 1.000 prueba oficial |
| Lote de prueba del cargador | imágenes 8×3×256×256 y máscaras 8×1×256×256 |

La partición es determinista (semilla 42): en una ejecución limpia, sin PyTorch, los archivos `particion/*.csv` y `eda_resumen.json` salieron idénticos byte a byte a los del primer análisis. Archivos que se generan en `salida_sprint1/` (no se sube a Git): `figuras_eda/`, `eda_resumen.json`, `particion/` (con `config_preparacion.json`), `lote_de_prueba.png` y `notebooks_ejecutados/`.

Detalles y hallazgos en el README de `Sprint 1 - Notebooks/`.

## Estado
Los notebooks del Sprint 1 se ejecutaron con el dataset real y las cifras (6.000 imágenes, 4.793 pares de segmentación, cantidades por clase) coinciden con el artículo; las diferencias menores (planos de corte, máscaras no binarias, tamaños variables, duplicados) están en el README de `Sprint 1 - Notebooks/`. Los campos marcados `[completar]` en los documentos los llena el equipo con el avance real.
