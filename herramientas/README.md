# Herramientas

Generadores que se usaron para producir el informe y las presentaciones del Sprint 1. Usan rutas relativas al repositorio.
Requieren `python-docx`, `python-pptx`, `lxml`, `matplotlib`, `pandas` y `pillow` (`pip install python-docx python-pptx lxml matplotlib pandas pillow`),
y haber ejecutado antes el Sprint 1 (`python ejecutar_sprint1.py` y `python perfil_datos.py`) para tener `salida_sprint1/`.

| Script | Qué hace |
|---|---|
| `gen_figs.py` | Gráficos del informe y de las diapositivas (sector, escenario, prevalencia, modo de archivo, entrenamiento vs prueba, partición) en `herramientas/figs/` |
| `build_informe.py` | Genera el informe del Sprint 1 en Word (`herramientas/informe_sprint1.docx`); luego se convierte a PDF (por ejemplo con LibreOffice) |
| `deck_light.py` | Genera `Revisión del Sprint.pptx` y `Retrospectiva del Sprint.pptx` con diseño blanco; **sobrescribe** los de `04. Revision y retrospectiva/` |

Orden: `python gen_figs.py` → `python build_informe.py` / `python deck_light.py`.
Estilo: fondo blanco, formal; paleta `#1F3864 #5B84B1 #2B7A8B #8FB89A #9AA5B1`; sin naranja. No son parte del modelo ni hace falta ejecutarlos para el Sprint 2.
