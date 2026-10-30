# CLAUDE.md — contexto del proyecto (léelo primero)

Proyecto académico de Redes Neuronales (Ingeniería de Sistemas – Inteligencia Artificial). Equipo de 4 estudiantes; el docente
(Ing. Hugo Espetia Huamanga) solo revisa. Metodología híbrida **Scrum + CRISP-ML(Q)**. Responde siempre en **español**.

**Título:** Desarrollo de un Sistema Inteligente para clasificar y segmentar tumores cerebrales en resonancias magnéticas (¿para qué?),
desplegado en una aplicación web de apoyo académico (¿para dónde?). Es una demostración académica, **no** una herramienta de diagnóstico.

- Repositorio: https://github.com/Calamar49/CNN-BRISC
- Tablero Scrum (Trello, privado): https://trello.com/b/swXjkoyS/product-backlog-proyecto-redes-neuronales-brisc
- Dataset: BRISC 2025 — https://www.kaggle.com/datasets/briscdataset/brisc2025/ · artículo https://arxiv.org/abs/2506.14318 · licencia CC BY 4.0 (citar a los autores)
- **Plan vigente: `docs/PLAN_SPRINT3.md`** (Sprint 3: evaluación en la prueba, sistema web con el flujo principal de apoyo al diagnóstico, MLOps, informe, exposición y cierre). **Léelo después de este archivo.**
- Contexto del Sprint 2 (entorno, versiones, protocolo de modelado): `docs/TRASPASO_SPRINT2.md`.

## Estado (29 de octubre de 2026)
- **Sprint 1 terminado** (1–8 oct, presentado el 12 oct): comprensión del negocio, comprensión de los datos y preparación de los datos. No se entrenó ningún modelo.
- **Sprint 2 (modelado), parte técnica hecha** (HU05 a HU09): código, 13 entrenamientos y modelos elegidos en `03. Implementacion/Sprint 2 - Entrenamiento/`, con métricas de **validación**; la prueba oficial no se tocó. Falta su gestión (Trello, Excel, informe de estado, minuta, riesgos, retrospectiva) y subir su informe y presentación.
- **Sprint 3 (24–29 oct) es lo que sigue:** evaluación única en la prueba oficial (HU12), sistema web (HU13), MLOps básico (HU14), informe final (HU15), exposición (HU16) y presentación final (HU17). Presentación final 30 oct, margen 31 oct, **fecha límite 2 nov 2026**. El despliegue acordado: **sistema web tipo clínica (prototipo)** con el **flujo principal de apoyo al diagnóstico completo y profesional** y los demás módulos como maqueta; datos ficticios; decir «apoyo al diagnóstico», no «diagnostica».

## Reglas que hay que respetar
1. **No inventar datos.** Todo número debe venir de una medición del proyecto o de una fuente citada; lo propuesto por el equipo se llama «propuesta». Los resultados del artículo de BRISC son del artículo, no nuestros.
2. **No hay patrocinador ni Dueño del Producto.** Solo el equipo; el docente revisa.
3. **La prueba oficial (1.000 imágenes) no se usa para elegir nada.** Se evalúa una sola vez, en HU12. Entrenar y comparar solo con entrenamiento y validación.
4. **No cambiar la partición** (semilla 42, 3.999 / 1.001 / 1.000, grupos por hash). Está en `03. Implementacion/Sprint 1 - Notebooks/salida_sprint1/particion/` y en el dataset preparado.
5. **No subir al repositorio** el dataset, pesos de modelos (`*.pt`, `*.pth`, `*.ckpt`), ni credenciales de Kaggle. Nunca pegar tokens en un chat.
6. Mantener el **formato de carpetas numeradas** del repositorio del docente (`01. Inicio` … `06. Cierre`) y los nombres de archivo de las plantillas.
7. **Presentaciones:** fondo blanco, formales y elegantes, sin naranja (generador en `herramientas/deck_light.py`). Gráficos con la paleta `#1F3864 #5B84B1 #2B7A8B #8FB89A #9AA5B1`.
8. Los resultados deben ser **reproducibles**: semilla fija, configuración guardada, comandos en un README.

## Estructura del repositorio
```
01. Inicio/                 Acta de Constitución (firmada), Backlog del Producto, Registro de Interesados, Planificación de Lanzamiento
02. Planificacion/          Backlog Detallado, Backlog del Sprint, Cronograma de hitos, Presupuesto, Registro de Riesgos, CSV del Gantt
03. Implementacion/         Informe de Estado, Minuta, Registro de Impedimentos, Informe del Sprint 1 (.docx y .pdf)
   Sprint 1 - Notebooks/    notebooks HU02 y HU03 y scripts (descargar, ejecutar, perfil, preparar y verificar dataset)
04. Revision y retrospectiva/  Revisión del Sprint (29 diapositivas) y Retrospectiva (plantilla con campos por llenar)
05. Lanzamiento/, 06. Cierre/  plantillas del docente sin llenar (se usan al final)
herramientas/               generadores del informe y de las presentaciones (ver su README)
docs/PLAN_SPRINT3.md        plan del Sprint 3 y del sistema web
docs/TRASPASO_SPRINT2.md    guía de trabajo del Sprint 2
```

## Datos (en el equipo de quien trabaje, fuera de OneDrive y de Git)
- Original: `~/datasets/brisc2025` → se baja con `python descargar_brisc.py` (carpeta `03. Implementacion/Sprint 1 - Notebooks`).
- **Preparado: `~/datasets/brisc2025_preparado`** → `python preparar_dataset.py` y `python verificar_preparado.py`. Imágenes y máscaras de 256×256, máscaras binarias 0/255,
  carpetas `imagenes/` y `mascaras/` por partición y clase, y `manifest_preparado.csv`. Aplicar la **normalización de ImageNet al cargar** (imagen en gris repetida en 3 canales).
- Resumen: 6.000 imágenes (3.999 entrenamiento, 1.001 validación, 1.000 prueba), 4 clases (glioma, meningioma, hipófisis, sin tumor), 4.793 máscaras. **Sin tumor no tiene máscara.**

## Hallazgos del Sprint 1 que condicionan el modelado
- Máscaras no binarias en origen → se binarizan con umbral > 127. Imágenes de 183 tamaños → relleno a cuadrado sin deformar y 256×256.
- El tumor ocupa en mediana 0,9 % (hipófisis) a 1,7 % (meningioma) de la imagen → usar pérdida robusta al desbalance (Dice o focal) en segmentación.
- El 8,3 % de las máscaras tiene más de una región; el glioma tiene contraste casi igual al tejido (mediana 1,07) → se espera que sea lo más difícil de segmentar.
- **Posible atajo por procedencia (riesgo R09, propuesto):** 100 % de «sin tumor» en RGB y 88 % de glioma en escala de grises; brillo y encuadre cambian con la clase.
  Mitigar con normalización de intensidad, aumento de brillo/contraste y reportar resultados por plano y por tipo de archivo.
- La prueba oficial **no es idéntica al entrenamiento** (más imágenes en gris, otro brillo y tamaño de tumor en algunas clases) y 113–123 de sus 1.000 imágenes tienen un vecino casi idéntico en entrenamiento → reportarlo al dar el resultado final.
- 96 archivos con SHA-256 repetido (7 entre entrenamiento y prueba), marcados en `duplicado_exacto`; no se eliminaron.

## Metas del acta (propuestas del equipo, aún sin evaluar; solo sobre la prueba oficial)
Accuracy ≥ 95 %, recall ≥ 90 % en cada clase, IoU ≥ 70 % (segmentación, solo imágenes con tumor).

## Entorno de referencia
Windows 11 · Python 3.13.14 · GPU NVIDIA RTX 4050 Laptop (6 GB, controlador 610.78) · el PyTorch instalado (2.13.0) es **solo CPU**: instalar la versión con CUDA (ver `docs/TRASPASO_SPRINT2.md`).
Versiones probadas del Sprint 1 en `requirements-probado.txt`.

## Cómo trabajar con este repositorio
- Antes de proponer algo, lee `docs/PLAN_SPRINT3.md`, `docs/TRASPASO_SPRINT2.md` y el informe `03. Implementacion/Informe del Sprint 1.pdf`.
- Código nuevo del Sprint 2 en `03. Implementacion/Sprint 2 - Entrenamiento/`; resultados en `salida_sprint2/` (ignorada por Git).
- Cada experimento se registra en `experimentos.csv` (columnas en el documento de traspaso). Commits en español, claros y pequeños.
- Además del modelado, cada sprint deja evidencia de gestión (backlog del sprint, Trello, informe de estado, minuta, riesgos, presentación y retrospectiva con el equipo): ver la sección 15 de `docs/TRASPASO_SPRINT2.md`.
- Si algo del traspaso no coincide con lo que ves en el repositorio o en Trello, **pregunta al equipo** antes de asumir.
