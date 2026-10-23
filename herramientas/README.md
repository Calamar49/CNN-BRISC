# Herramientas

Generadores que se usaron para producir los informes y las presentaciones de los sprints. Usan rutas relativas al repositorio.
Requieren `python-docx`, `python-pptx`, `lxml`, `matplotlib`, `pandas` y `pillow` (`pip install python-docx python-pptx lxml matplotlib pandas pillow`).

**Sprint 1** (requieren haber ejecutado antes `python ejecutar_sprint1.py` y `python perfil_datos.py`, para tener `salida_sprint1/`):

| Script | Qué hace |
|---|---|
| `gen_figs.py` | Gráficos del informe y de las diapositivas (sector, escenario, prevalencia, modo de archivo, entrenamiento vs prueba, partición) en `herramientas/figs/` |
| `build_informe.py` | Genera el informe del Sprint 1 en Word (`herramientas/informe_sprint1.docx`); luego se convierte a PDF (por ejemplo con LibreOffice) |
| `deck_light.py` | Genera `Revisión del Sprint.pptx` y `Retrospectiva del Sprint.pptx` con diseño blanco; **sobrescribe** los de `04. Revision y retrospectiva/` |

Orden: `python gen_figs.py` → `python build_informe.py` / `python deck_light.py`.

**Sprint 2** (requieren haber entrenado los modelos de `03. Implementacion/Sprint 2 - Entrenamiento/`, para tener `salida_sprint2/` y `experimentos.csv`):

| Script | Qué hace |
|---|---|
| `gen_figs_sprint2.py` | Gráficos reales del Sprint 2 (curvas de entrenamiento, matriz de confusión, comparación de configuraciones HU08, desglose R09) en `herramientas/figs_sprint2/`. No inventa datos: todo sale de `salida_sprint2/*.csv` y `experimentos.csv`. |
| `gen_figs_sprint2_extra.py` | Gráficos reales adicionales en la misma carpeta: IoU/Dice de la U-Net por clase y por plano, recall por clase comparando EfficientNetB0 vs ResNet50, tiempo de entrenamiento de las 13 corridas, curvas de IoU superpuestas de las 4 configuraciones de HU08 de la U-Net, una muestra real de 8 imágenes del dataset preparado, y una captura (imagen) de la salida real de `verificar_preparado.py`. Independiente de `gen_figs_sprint2.py`: no lo modifica. |
| `build_informe_sprint2.py` | Genera el informe del Sprint 2 en Word (`herramientas/informe_sprint2.docx`): metodología, resultados de HU05 a HU09 con las figuras anteriores, desglose por clase/plano/tipo de archivo, limitaciones y amenazas a la validez, y glosario. Todo a partir de `experimentos.csv`, `docs/TRASPASO_SPRINT2.md` y el README de `Sprint 2 - Entrenamiento/`. |
| `build_slides_sprint2.py` | Genera `herramientas/presentacion_sprint2.pptx` (18 diapositivas) para la Revisión del Sprint 2, reutilizando el estilo de `deck_light.py` (mismos colores, fuente y tamaño; no lo modifica). Cada cifra se lee de `experimentos.csv` en tiempo de ejecución. |

Orden: `python gen_figs_sprint2.py` → `python gen_figs_sprint2_extra.py` → `python build_informe_sprint2.py` / `python build_slides_sprint2.py`.

Estilo: fondo blanco, formal; paleta `#1F3864 #5B84B1 #2B7A8B #8FB89A #9AA5B1`; sin naranja. Los `.docx` y las carpetas de
figuras generadas no se suben a Git (son reproducibles con estos scripts); solo se sube el código.
