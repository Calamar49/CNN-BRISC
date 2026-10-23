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
| `build_informe_sprint2.py` | Genera el informe del Sprint 2 en Word (`herramientas/informe_sprint2.docx`) con esas figuras y la tabla completa de `experimentos.csv`. |

Orden: `python gen_figs_sprint2.py` → `python build_informe_sprint2.py`.

Estilo: fondo blanco, formal; paleta `#1F3864 #5B84B1 #2B7A8B #8FB89A #9AA5B1`; sin naranja. Los `.docx` y las carpetas de
figuras generadas no se suben a Git (son reproducibles con estos scripts); solo se sube el código.
