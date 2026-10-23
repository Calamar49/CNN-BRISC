# -*- coding: utf-8 -*-
"""Genera el Informe del Sprint 2 (docx) a partir de los resultados reales en
"03. Implementacion/Sprint 2 - Entrenamiento/experimentos.csv" y de las figuras de gen_figs_sprint2.py.

Uso:
    python gen_figs_sprint2.py      # genera las figuras (lee salida_sprint2/*.csv)
    python build_informe_sprint2.py # arma el docx con esas figuras y el experimentos.csv
"""
import json
import re
from pathlib import Path as _P

import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

_AQUI = _P(__file__).resolve().parent
_RAIZ = _AQUI.parent
S2 = _RAIZ / "03. Implementacion" / "Sprint 2 - Entrenamiento"
FIGS = _AQUI / "figs_sprint2"
OUT = str(_AQUI / "informe_sprint2.docx")

NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2F, 0x55, 0x97)
TEAL = RGBColor(0x2B, 0x7A, 0x8B)
GRAY = RGBColor(0x59, 0x59, 0x59)

exp = pd.read_csv(S2 / "experimentos.csv")

d = Document()
sec = d.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)

st = d.styles["Normal"]
st.font.name = "Calibri"
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.font.size = Pt(10.5)
st.paragraph_format.space_after = Pt(6)
st.paragraph_format.line_spacing = 1.12
for name, size, color, before, after in (("Heading 1", 17, NAVY, 20, 8), ("Heading 2", 13, BLUE, 14, 5), ("Heading 3", 11, NAVY, 10, 3)):
    h = d.styles[name]
    h.font.name = "Calibri"
    h.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    h.element.rPr.rFonts.set(qn("w:ascii"), "Calibri")
    h.element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = color
    h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(after)
    h.paragraph_format.keep_with_next = True


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def cell_margins(tbl, top=50, bottom=50, left=90, right=90):
    tblPr = tbl._tbl.tblPr
    m = OxmlElement("w:tblCellMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); m.append(e)
    tblPr.append(m)


def borders(tbl, color="BFBFBF"):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for k in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{k}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
        b.append(e)
    tblPr.append(b)


def H1(t): return d.add_heading(t, 1)
def H2(t): return d.add_heading(t, 2)
def H3(t): return d.add_heading(t, 3)


def add_rich(p, text, bold=False, italic=False, size=None, color=None):
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        r = p.add_run(part)
        r.bold = bold or (i % 2 == 1)
        r.italic = italic
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color


def P(text="", bold=False, italic=False, size=None, color=None, align=None, after=None, keep=False):
    p = d.add_paragraph()
    add_rich(p, text, bold, italic, size, color)
    if align: p.alignment = align
    if after is not None: p.paragraph_format.space_after = Pt(after)
    if keep: p.paragraph_format.keep_with_next = True
    return p


def B(text, level=0):
    p = d.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.63 + 0.6 * level)
    p.paragraph_format.first_line_indent = Cm(-0.5)
    p.paragraph_format.space_after = Pt(3)
    add_rich(p, text)
    return p


_fig_n = [0]


def T(rows, widths, header=True, size=9, zebra=True):
    tbl = d.add_table(rows=len(rows), cols=len(rows[0]))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    borders(tbl); cell_margins(tbl)
    for j, wcm in enumerate(widths):
        tbl.columns[j].width = Cm(wcm)
    for i, row in enumerate(rows):
        tr = tbl.rows[i]
        for j, txt in enumerate(row):
            c = tr.cells[j]
            c.width = Cm(widths[j])
            p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.05
            is_head = header and i == 0
            add_rich(p, str(txt), bold=is_head, size=size, color=RGBColor(255, 255, 255) if is_head else None)
            if is_head:
                shade(c, "1F3864")
            elif zebra and i % 2 == 0:
                shade(c, "F2F5FA")
    d.add_paragraph().paragraph_format.space_after = Pt(2)
    return tbl


def FIG(path, width_cm, caption):
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    c = d.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _fig_n[0] += 1
    caption = "Figura %d. " % _fig_n[0] + re.sub(r"^Figura \d+\. ", "", caption)
    add_rich(c, caption, italic=True, size=9, color=GRAY)
    c.paragraph_format.space_after = Pt(10)


def NOTE(text):
    t = d.add_table(rows=1, cols=1)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    cell_margins(t, 90, 90, 160, 160)
    c = t.rows[0].cells[0]
    c.width = Cm(16.6)
    shade(c, "EAF0FA")
    tcPr = c._tc.get_or_add_tcPr()
    bd = OxmlElement("w:tcBorders")
    e = OxmlElement("w:left"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "24"); e.set(qn("w:color"), "2F5597"); bd.append(e)
    tcPr.append(bd)
    p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
    add_rich(p, text, size=10)
    d.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break():
    d.add_page_break()


def add_field(run, instr):
    for kind, txt in (("begin", None), (None, instr), ("end", None)):
        if kind:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind); run._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; run._r.append(e)


fp = sec.footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run("Informe del Sprint 2 · Sistema Inteligente: tumores cerebrales en MRI · Página ")
r.font.size = Pt(8.5); r.font.color.rgb = GRAY
r2 = fp.add_run(); r2.font.size = Pt(8.5); r2.font.color.rgb = GRAY
add_field(r2, "PAGE")
sec.different_first_page_header_footer = True

# ================================================================ helpers de datos
def recall_medio(celda):
    try:
        return float(pd.Series(json.loads(celda)).mean())
    except Exception:
        return None


exp["recall_medio"] = exp.val_recall_por_clase.apply(lambda c: recall_medio(c) if isinstance(c, str) else None)
clf_hu06 = exp[(exp.tarea == "clasificacion") & (exp.historia == "HU06")]
unet_hu07 = exp[(exp.tarea == "segmentacion") & (exp.historia == "HU07")]
clf_hu08 = exp[(exp.tarea == "clasificacion") & (exp.historia == "HU08")]
unet_hu08 = exp[(exp.tarea == "segmentacion") & (exp.historia == "HU08")]
clf_semillas = clf_hu08[clf_hu08.batch == 64]
unet_semillas = unet_hu08[unet_hu08.lr == 0.0001]

# ================================================================ PORTADA
for _ in range(3):
    d.add_paragraph()
band = d.add_table(rows=1, cols=1)
band.alignment = WD_TABLE_ALIGNMENT.CENTER
band.autofit = False
cell_margins(band, 300, 300, 300, 300)
c = band.rows[0].cells[0]
c.width = Cm(16.6)
shade(c, "1F3864")
p = c.paragraphs[0]
add_rich(p, "INFORME DEL SPRINT 2", bold=True, size=30, color=RGBColor(255, 255, 255))
p.paragraph_format.space_after = Pt(6)
p = c.add_paragraph()
add_rich(p, "Modelado: clasificación y segmentación de tumores cerebrales", size=14, color=RGBColor(0xC9, 0xD6, 0xEC))
p.paragraph_format.space_after = Pt(0)

d.add_paragraph()
P("Desarrollo de un Sistema Inteligente para clasificar y segmentar tumores cerebrales en resonancias "
  "magnéticas (¿para qué?), desplegado en una aplicación web de apoyo académico (¿para dónde?)",
  bold=True, size=13, color=NAVY, after=14)

T([["Proyecto", "Proyecto académico de Redes Neuronales – Opción B (Ingeniería de Sistemas, Inteligencia Artificial)"],
   ["Metodología", "Híbrida: Scrum + CRISP-ML(Q) — fase de modelado"],
   ["Sprint", "Sprint 2 (10–22 oct 2026), presentación 23 oct 2026"],
   ["Docente revisor", "Ing. Hugo Espetia Huamanga"],
   ["Dataset", "BRISC 2025 (Kaggle, CC BY 4.0) — 6.000 imágenes, 4.793 máscaras"],
   ["Repositorio", "github.com/Calamar49/CNN-BRISC"]], [4.5, 12.1])

d.add_paragraph()
T([["Integrante", "Rol (propuesta)"],
   ["Coavoy Cruz Joseph Gabriel", "Gerente de Proyecto"],
   ["Cuchuyrrumi Mamani Manuel Rodrigo", "Scrum Master"],
   ["Huallpatuiro Rafaile Brayan", "Equipo de desarrollo"],
   ["Mamani Acuña Frank Joseph", "Equipo de desarrollo"]], [10, 6.6])

P("Este documento es una demostración académica; no es una herramienta de diagnóstico médico. Todos los "
  "números provienen de mediciones reales del equipo sobre el conjunto de validación (ver experimentos.csv); "
  "las cifras del artículo de BRISC se citan como tales, no como resultados propios.", italic=True, size=9.5, color=GRAY)
page_break()

# ================================================================ 1. RESUMEN EJECUTIVO
H1("1. Resumen ejecutivo")
P("El Sprint 1 dejó el dataset BRISC 2025 descargado, analizado y preparado (256×256, máscaras binarias, "
  "partición propia 3.999/1.001/1.000 con semilla 42), pero **sin ningún modelo entrenado**. Este Sprint 2 "
  "construyó el pipeline de modelado completo y entrenó, ajustó y comparó modelos reales para las dos tareas "
  "del sistema: clasificación del tipo de tumor (4 clases) y segmentación de su contorno.")
B(f"**Clasificación (HU05/HU06):** se compararon 2 arquitecturas con transfer learning (EfficientNetB0 y "
  f"ResNet50). El modelo elegido, EfficientNetB0, promedia **{clf_semillas.recall_medio.mean()*100:.2f} % "
  f"de recall** en validación sobre 3 semillas.")
B(f"**Segmentación (HU07):** U-Net con encoder ResNet34 preentrenado, entrenada solo con imágenes que tienen "
  f"máscara. El modelo elegido promedia **{unet_semillas.val_iou.mean()*100:.2f} % de IoU** sobre 3 semillas.")
B("**HU08:** se probaron 3 configuraciones adicionales por tarea (tasa de aprendizaje, tamaño de lote, sin "
  "aumento de datos) frente al modelo base; se repitió el entrenamiento final con 2 semillas más.")
B(f"**HU09:** {len(exp)} entrenamientos quedaron registrados con su configuración, métricas y tiempo en "
  "experimentos.csv (tabla completa en la sección 7).")
B("Ambos modelos superan las metas del acta de constitución (accuracy ≥ 95 %, recall ≥ 90 % por clase, "
  "IoU ≥ 70 %), medidas **solo sobre validación** — la prueba oficial (1.000 imágenes) no se tocó y se "
  "evaluará una única vez en el Sprint 3 (HU12).")
NOTE("**Qué falta:** la gestión Scrum del sprint (Backlog en Trello/Excel, Informe de Estado, Registro de "
     "Riesgos con R09, Retrospectiva) y la presentación del Sprint 2 (HU10) — quedan a cargo del equipo.")

# ================================================================ 2. METODOLOGIA Y ENTORNO
H1("2. Metodología y entorno")
H2("2.1 CRISP-ML(Q) — fase de modelado")
P("Para la fase de modelado, CRISP-ML(Q) pide definir requisitos y restricciones, identificar riesgos y "
  "mitigarlos, seleccionar modelos de forma documentada y dejar todo reproducible.")
B("**Requisitos:** metas del acta (accuracy ≥ 95 %, recall ≥ 90 % por clase, IoU ≥ 70 %).")
B("**Restricciones:** GPU de 8 GB, solo imágenes T1 con contraste, plazos del cronograma.")
B("**Selección de modelos:** documentada en experimentos.csv, con la elección justificada por desempeño "
  "promedio en validación (sección 6).")
B("**Reproducibilidad:** semilla fija por corrida, configuración y checkpoint guardados, comandos en el "
  "README de `Sprint 2 - Entrenamiento/`.")
B("**Sin fuga hacia la evaluación:** la prueba oficial no se usó para elegir arquitectura, hiperparámetros "
  "ni época; solo se usó entrenamiento y validación.")

H2("2.2 Entorno de ejecución")
T([["Variable", "Valor"],
   ["Sistema operativo", "Windows 11"],
   ["Python", "3.12.8"],
   ["GPU", "NVIDIA GeForce RTX 5060 Laptop (8 GB)"],
   ["PyTorch", "2.11.0+cu128 (con CUDA)"],
   ["Librerías clave", "torchvision, segmentation-models-pytorch, timm"],
   ["Precisión", "mixta (torch.autocast) en todas las corridas"]], [6, 10.6])

H2("2.3 Datos")
P("Dataset BRISC 2025 preparado en el Sprint 1: 6.000 imágenes de 256×256 en un canal, 4.793 con máscara "
  "binaria, repartidas en 4 clases (glioma, meningioma, tumor de hipófisis y sin tumor). Las imágenes "
  "originales venían en 183 combinaciones distintas de tamaño y se llevaron a 256×256 con relleno a "
  "cuadrado sin deformar (interpolación bilineal en la imagen, *nearest* en la máscara, binarizada después "
  "con umbral > 127). Partición propia (semilla 42, agrupada por `grupo_hash` para no partir entre "
  "conjuntos imágenes casi idénticas): 3.999 entrenamiento, 1.001 validación (≈20 % por clase y plano) y "
  "1.000 prueba oficial, que no se tocó en ningún momento de este sprint. La segmentación usa solo las "
  "imágenes con máscara: 3.146 en entrenamiento y 787 en validación (las «sin tumor» no tienen máscara y "
  "quedan fuera de esa tarea). Normalización de ImageNet (media 0,485/0,456/0,406, desvío "
  "0,229/0,224/0,225) aplicada al cargar, sobre la imagen en gris repetida en 3 canales.")
T([["Clase", "Entrenamiento", "Validación", "Prueba oficial", "Con máscara (train/val/prueba)"],
   ["Glioma", "917", "230", "254", "917 / 230 / 254"],
   ["Meningioma", "1.063", "266", "306", "1.063 / 266 / 306"],
   ["Hipófisis", "1.166", "291", "300", "1.166 / 291 / 300"],
   ["Sin tumor", "853", "214", "140", "— (no tiene máscara)"],
   ["Total", "3.999", "1.001", "1.000", "3.146 / 787 / 860"]], [2.6, 2.7, 2.4, 2.7, 6.2])
P("Conteos del manifiesto preparado (`manifest_preparado.csv`, Sprint 1); coinciden exactamente con los "
  "que confirma `verificar_preparado.py` (figura siguiente). El tumor ocupa en mediana entre el 0,9 % "
  "(hipófisis) y el 1,7 % (meningioma) del área de la imagen, hallazgo del Sprint 1 que motivó usar una "
  "pérdida robusta al desbalance en la segmentación (sección 4).", size=9.5, color=GRAY)
if (FIGS / "muestra_dataset.png").exists():
    FIG(FIGS / "muestra_dataset.png", 15, "Mosaico real de 8 imágenes de resonancia magnética del dataset "
        "preparado, 2 por clase, tomadas de la partición de entrenamiento en disco "
        "(`imagenes/train/<clase>/`, misma raíz que usa `datos.py`); sin ningún retoque.")

H2("2.4 Verificación del entorno de datos")
P("Antes de entrenar cualquier modelo de este sprint se volvió a ejecutar `verificar_preparado.py` con el "
  "intérprete del proyecto, para confirmar que el dataset preparado en disco no hubiera cambiado desde el "
  "Sprint 1: conteos totales, partición por clase y plano, formato de las máscaras y coincidencia con la "
  "muestra del cargador del notebook `02_HU03`.")
if (FIGS / "terminal_verificacion.png").exists():
    FIG(FIGS / "terminal_verificacion.png", 15, "Salida real de la terminal al ejecutar "
        "`verificar_preparado.py` (captura del 23 de octubre de 2026), sin reescribir ni resumir el texto; "
        "termina en «RESULTADO: todo correcto».")
page_break()

# ================================================================ 3. HU05/HU06 CLASIFICADOR
H1("3. Clasificación del tipo de tumor (HU05, HU06)")
P("Se compararon dos arquitecturas con transfer learning (pesos de ImageNet), cambiando la última capa a "
  "4 salidas (glioma, meningioma, hipófisis, sin tumor): EfficientNetB0 (red compacta, del orden de 5 "
  "millones de parámetros) y ResNet50 (red más profunda, del orden de 25 millones de parámetros) — ambas "
  "descritas en sus publicaciones originales y las dos con mejor desempeño reportado en el artículo de "
  "BRISC. Entrada: imagen en gris repetida en 3 canales, 256×256, normalización de ImageNet.")
P("**Pérdida — entropía cruzada:** para cada imagen compara la probabilidad que el modelo asigna a la "
  "clase correcta contra el valor ideal de 1; cuanto más lejos está esa probabilidad de 1 (más seguro está "
  "el modelo de una clase equivocada), mayor el castigo. **Optimización:** AdamW ajusta los pesos con un "
  "tamaño de paso que sigue un *cosine schedule* (baja suavemente a lo largo del entrenamiento) y añade una "
  "pequeña penalización al tamaño de los pesos para reducir el sobreajuste. La **parada temprana** detiene "
  "el entrenamiento si el recall medio de validación no mejora en 5 épocas seguidas (paciencia 5), y la "
  "**precisión mixta** (`torch.autocast`) acelera el cómputo en la GPU sin tocar la arquitectura ni, en la "
  "práctica, el resultado.")

H2("3.1 Modelo base (semilla 42)")
rows = [["Arquitectura", "Época óptima", "val_accuracy", "val_recall medio", "val_F1 macro", "Tiempo"]]
for _, r in clf_hu06.iterrows():
    rows.append([r.arquitectura, f"{r.epoca_optima}/{r.epocas}", f"{r.val_accuracy*100:.1f} %",
                 f"{r.recall_medio*100:.2f} %", f"{r.val_f1_macro*100:.2f} %", f"{r.tiempo_min:.1f} min"])
T(rows, [4.2, 2.6, 2.6, 3.0, 2.6, 1.6])
P("Ambas arquitecturas superan la meta del acta (accuracy ≥ 95 %, recall ≥ 90 %). EfficientNetB0 se eligió "
  "como base por mejor recall medio y menor tiempo de entrenamiento.")

H2("3.2 Recall por clase en las 7 corridas de clasificación")
P("El recall por clase es la métrica más exigente del acta (≥ 90 % en cada una de las 4 clases), porque una "
  "sola clase débil no se diluye en un promedio. La figura siguiente compara EfficientNetB0 y ResNet50 "
  "(HU06, semilla 42) clase por clase; la tabla reúne las 7 corridas de clasificación de `experimentos.csv` "
  "(no solo el resumen de la sección 3.1), con el recall real de cada una de las 4 clases.")
if (FIGS / "recall_por_clase_arquitecturas.png").exists():
    FIG(FIGS / "recall_por_clase_arquitecturas.png", 15, "Recall de validación por clase de tumor, "
        "EfficientNetB0 vs. ResNet50 (filas historia=HU06 de experimentos.csv, columna "
        "val_recall_por_clase). Meningioma es la clase más baja en ambas arquitecturas; ResNet50 falla más "
        "en «sin tumor» (99,07 %) y EfficientNetB0 en «hipófisis» (99,66 %).")
clf_todas = exp[exp.tarea == "clasificacion"].copy()
clf_todas["recall_clase"] = clf_todas.val_recall_por_clase.apply(json.loads)
rows = [["Corrida", "Semilla", "Glioma", "Meningioma", "Hipófisis", "Sin tumor", "Recall medio"]]
_etiquetas_clf = {
    "clf_efficientnet_b0_20261022_235632": "HU06 base — EfficientNetB0",
    "clf_resnet50_20261023_000153": "HU06 — ResNet50",
    "clf_efficientnet_b0_20261023_002327": "HU08 — lr=1e-4",
    "clf_efficientnet_b0_20261023_002839": "HU08 — batch=64 (elegida)",
    "clf_efficientnet_b0_20261023_003302": "HU08 — sin aumento (ablación)",
    "clf_efficientnet_b0_20261023_004200": "Multi-semilla — batch=64",
    "clf_efficientnet_b0_20261023_004900": "Multi-semilla — batch=64",
}
for _, r in clf_todas.iterrows():
    rc = r.recall_clase
    rows.append([_etiquetas_clf.get(r.id, r.id), str(r.semilla),
                 f"{rc['glioma']*100:.2f} %", f"{rc['meningioma']*100:.2f} %",
                 f"{rc['pituitary']*100:.2f} %", f"{rc['no_tumor']*100:.2f} %",
                 f"{r.recall_medio*100:.2f} %"])
T(rows, [4.6, 1.6, 2.1, 2.2, 2.1, 2.1, 1.9], size=8.3)
_min_largo = [(c, v, r.id) for _, r in clf_todas.iterrows() for c, v in r.recall_clase.items()]
_min_clase, _min_val, _min_id = min(_min_largo, key=lambda t: t[1])
P("Las 4 clases superan el 90 % de recall en las 7 corridas; el valor mínimo de toda la tabla es "
  f"{_min_val*100:.2f} % ({_etiquetas_clf.get(_min_id, _min_id).lower()}, clase {_min_clase}), muy por "
  "encima de la meta del acta.", size=9.5, color=GRAY)

H2("3.3 Curva de entrenamiento real")
if (FIGS / "curva_clasificador.png").exists():
    FIG(FIGS / "curva_clasificador.png", 16, "Pérdida de entrenamiento y métricas de validación por época — "
        "EfficientNetB0, configuración ganadora de HU08 (batch=64), semilla 42. Datos reales de "
        f"{clf_semillas[clf_semillas.semilla == 42].iloc[0]['id'] if (clf_semillas.semilla == 42).any() else 'la corrida'}.")

H2("3.4 Matriz de confusión (validación)")
if (FIGS / "matriz_confusion.png").exists():
    FIG(FIGS / "matriz_confusion.png", 10, "Matriz de confusión real sobre las 1.001 imágenes de validación "
        "(checkpoint ganador, semilla 42).")
page_break()

# ================================================================ 4. HU05/HU07 SEGMENTACION
H1("4. Segmentación del tumor (HU05, HU07)")
P("U-Net con encoder ResNet34 preentrenado (ImageNet), vía `segmentation-models-pytorch`: el encoder reduce "
  "la imagen a mapas de características cada vez más pequeños y abstractos (como un clasificador), y un "
  "decodificador simétrico los vuelve a ampliar hasta el tamaño original, combinando en cada paso los "
  "detalles finos guardados por el encoder (conexiones salteadas) para dibujar un contorno preciso en vez "
  "de solo decir «hay tumor en algún lado». Entrenada **solo con las imágenes que tienen máscara** (sin "
  "tumor queda fuera, no tiene nada que segmentar).")
P("**Pérdida — BCE + Dice:** se suman dos términos por cada píxel. La entropía cruzada binaria (BCE) "
  "compara la probabilidad de tumor que predice el modelo contra 0 o 1 en ese píxel, tratando a cada uno "
  "por separado. La pérdida de Dice compara, para la imagen completa, cuánto se solapa el área predicha con "
  "la real frente al tamaño de ambas juntas; este segundo término es el que más ayuda cuando el tumor es "
  "una fracción pequeña de la imagen (mediana 0,9–1,7 %, hallazgo del Sprint 1), porque la BCE sola tiende "
  "a predecir todo fondo y aun así obtener una pérdida baja. Umbral de salida 0,5 sobre la probabilidad por "
  "píxel; aumento de datos aplicado igual en la imagen y en la máscara (mismo giro, misma rotación), para "
  "que sigan calzando una con otra.")

H2("4.1 Modelo base (semilla 42)")
rows = [["Encoder", "Época óptima", "val_IoU", "val_Dice", "Tiempo"]]
for _, r in unet_hu07.iterrows():
    rows.append(["ResNet34", f"{r.epoca_optima}/{r.epocas}", f"{r.val_iou*100:.2f} %",
                 f"{r.val_dice*100:.2f} %", f"{r.tiempo_min:.1f} min"])
T(rows, [3.5, 3.3, 3.0, 3.0, 3.8])
P("Supera la meta del acta (IoU ≥ 70 %) y la referencia del artículo de BRISC (U-Net, 75,7 % mIoU — cifra "
  "del artículo, con otra partición, no comparable en igualdad de condiciones).")

H2("4.2 Curva de entrenamiento real")
if (FIGS / "curva_unet.png").exists():
    FIG(FIGS / "curva_unet.png", 16, "Pérdida de entrenamiento y métricas de validación por época — U-Net, "
        "configuración ganadora de HU08 (lr=1e-4), semilla 42.")

H2("4.3 Ejemplos reales de segmentación (validación)")
ejemplos = sorted(S2.glob("salida_sprint2/unet_resnet34_20261022_235636_ejemplos.png"))
if ejemplos:
    FIG(ejemplos[0], 13, "Imagen de validación, máscara real y máscara predicha por el modelo base — salida "
        "real del modelo, sin retocar. En 3 de 4 casos la predicción calza bien con la máscara real; en un "
        "caso (tumor muy pequeño y alargado) el modelo no predijo nada, consistente con el hallazgo del "
        "Sprint 1 sobre el tamaño mediano del tumor.")

H2("4.4 Desempeño por clase y por plano de corte")
_id_unet_grupo = unet_semillas[unet_semillas.semilla == 42].iloc[0]["id"]
_pg_path = S2 / "salida_sprint2" / f"{_id_unet_grupo}_por_grupo.csv"
if _pg_path.exists():
    pg = pd.read_csv(_pg_path)
    pg_clase = pg.groupby("clase")[["iou", "dice"]].mean().reindex(["glioma", "meningioma", "pituitary"])
    pg_clase_n = pg.groupby("clase").size().reindex(["glioma", "meningioma", "pituitary"])
    pg_plano = pg.groupby("plano")[["iou", "dice"]].mean().reindex(["ax", "co", "sa"])
    pg_plano_n = pg.groupby("plano").size().reindex(["ax", "co", "sa"])
    P("El promedio de IoU oculta que la dificultad no es la misma para las 3 clases con tumor ni para los 3 "
      "planos de corte. Se evaluó el checkpoint ganador de HU08 (ResNet34, lr=1e-4, semilla 42) imagen por "
      f"imagen sobre las {len(pg)} de validación con máscara, con `evaluar_grupos.py`, y se agrupó por clase "
      "y por plano (detalle por imagen en "
      f"`salida_sprint2/{_id_unet_grupo}_por_grupo.csv`).")
    if (FIGS / "iou_por_clase.png").exists():
        FIG(FIGS / "iou_por_clase.png", 13, "IoU y Dice medios de validación por clase de tumor — calculados "
            f"desde `{_id_unet_grupo}_por_grupo.csv` (columnas iou, dice, clase).")
    rows = [["Clase", "IoU medio", "Dice medio", "n (imágenes)"]]
    for c, et in (("glioma", "Glioma"), ("meningioma", "Meningioma"), ("pituitary", "Hipófisis")):
        rows.append([et, f"{pg_clase.loc[c, 'iou']*100:.2f} %", f"{pg_clase.loc[c, 'dice']*100:.2f} %",
                     str(pg_clase_n[c])])
    T(rows, [5.0, 3.6, 3.6, 4.4])
    B(f"**Glioma** es, con claridad, la clase más difícil de segmentar ({pg_clase.loc['glioma','iou']*100:.2f} % "
      "de IoU, frente a "
      f"{pg_clase.loc['meningioma','iou']*100:.2f} % de meningioma): coincide con el hallazgo del Sprint 1 de "
      "que su contraste con el tejido sano es casi igual (mediana 1,07), el más bajo de las 3 clases con "
      "tumor.")
    B(f"**Meningioma** es la más fácil ({pg_clase.loc['meningioma','iou']*100:.2f} % de IoU) y también la de "
      "mejor contraste medido en el Sprint 1 (mediana 1,52).")
    B(f"**Hipófisis** queda en medio ({pg_clase.loc['pituitary','iou']*100:.2f} % de IoU); al estar muy "
      "centrada y ser pequeña, el modelo la localiza bien pero el contorno exacto es más sensible al umbral "
      "de 0,5.")
    if (FIGS / "iou_por_plano.png").exists():
        FIG(FIGS / "iou_por_plano.png", 12, "IoU medio de validación por plano de corte — calculado desde "
            f"`{_id_unet_grupo}_por_grupo.csv` (columnas iou, plano).")
    rows = [["Plano", "IoU medio", "n (imágenes)"]]
    for p, et in (("ax", "Axial"), ("co", "Coronal"), ("sa", "Sagital")):
        rows.append([et, f"{pg_plano.loc[p, 'iou']*100:.2f} %", str(pg_plano_n[p])])
    T(rows, [5.0, 4.0, 4.0])
    P(f"El plano con menos IoU (axial, {pg_plano.loc['ax','iou']*100:.2f} %) y el de más IoU (sagital, "
      f"{pg_plano.loc['sa','iou']*100:.2f} %) difieren en "
      f"{(pg_plano.loc['sa','iou']-pg_plano.loc['ax','iou'])*100:.1f} puntos porcentuales — una diferencia "
      "menor que la que separa a glioma de meningioma por clase, así que el plano de corte pesa menos en el "
      "resultado que el tipo de tumor. El desglose por tipo de archivo (gris/RGB), relacionado con el riesgo "
      "R09, se discute en la sección 6.")
page_break()

# ================================================================ 5. HU08
H1("5. Ajuste de hiperparámetros (HU08)")
P("Se probaron 3 configuraciones adicionales por tarea frente al modelo base, comparando solo con "
  "validación (la prueba oficial no se usó para elegir nada).")

H2("5.1 Clasificador (EfficientNetB0)")
rows = [["Configuración", "val_recall medio", "Δ vs. base"]]
base_r = clf_hu06.recall_medio.iloc[0]
rows.append(["Base: lr=3e-4, batch=32, con aumento", f"{base_r*100:.2f} %", "—"])
for _, r in clf_hu08[clf_hu08.semilla == 42].iterrows():
    desc = ("lr=1e-4" if r.lr == 0.0001 else ("batch=64 (elegida)" if r.batch == 64 else "sin aumento (ablación)"))
    delta = (r.recall_medio - base_r) * 100
    rows.append([desc, f"{r.recall_medio*100:.2f} %", f"{delta:+.2f} pp"])
T(rows, [8, 4.3, 4.3])

H2("5.2 U-Net (encoder ResNet34)")
rows = [["Configuración", "val_IoU", "Δ vs. base"]]
base_i = unet_hu07.val_iou.iloc[0]
rows.append(["Base: lr=3e-4, batch=8, con aumento", f"{base_i*100:.2f} %", "—"])
for _, r in unet_hu08[unet_hu08.semilla == 42].iterrows():
    desc = ("lr=1e-4 (elegida)" if r.lr == 0.0001 else ("batch=16" if r.batch == 16 else "sin aumento (ablación)"))
    delta = (r.val_iou - base_i) * 100
    rows.append([desc, f"{r.val_iou*100:.2f} %", f"{delta:+.2f} pp"])
T(rows, [8, 4.3, 4.3])

if (FIGS / "curvas_unet_hu08.png").exists():
    FIG(FIGS / "curvas_unet_hu08.png", 15, "IoU de validación por época para las 4 configuraciones de la "
        "U-Net con semilla=42 (Base, lr=1e-4, sin aumento, batch=16), leyendo cada `<id>_curva.csv` de "
        "`salida_sprint2/` según `experimentos.csv`. Las 4 curvas suben rápido en las primeras 5 épocas y "
        "luego se estabilizan cerca de 78–80 % de IoU; «sin aumento» es visiblemente más irregular época a "
        "época que las otras 3, y «batch=16» es la que llega más alto hacia el final, aunque solo se corrió "
        "a una semilla (ver sección 8).")

if (FIGS / "hu08_comparacion.png").exists():
    FIG(FIGS / "hu08_comparacion.png", 16, "Comparación real de configuraciones de HU08 frente al modelo "
        "base, por tarea (datos de experimentos.csv).")
P("El aumento de datos mejora el resultado en ambas tareas (quitarlo lo empeora); el ajuste de tasa de "
  "aprendizaje y tamaño de lote aporta una mejora pequeña (menor a 1 punto porcentual) frente al modelo "
  "base, que ya estaba cerca del óptimo para este dataset y estas arquitecturas.")

H2("5.3 Entrenamiento final con semillas adicionales")
P("Se repitió la configuración ganadora de cada tarea con 2 semillas más, como pide la sección 6.1 del "
  "traspaso, para reportar un promedio y no un resultado de una sola corrida.")
rows = [["Modelo", "Semilla 42", "Semilla 123", "Semilla 2024", "Promedio ± desvío"]]
vals_clf = clf_semillas.set_index("semilla").recall_medio
rows.append(["EfficientNetB0, batch=64 (recall medio)", f"{vals_clf[42]*100:.2f} %", f"{vals_clf[123]*100:.2f} %",
             f"{vals_clf[2024]*100:.2f} %", f"**{vals_clf.mean()*100:.2f} % ± {vals_clf.std()*100:.2f} %**"])
vals_unet = unet_semillas.set_index("semilla").val_iou
rows.append(["U-Net, lr=1e-4 (IoU)", f"{vals_unet[42]*100:.2f} %", f"{vals_unet[123]*100:.2f} %",
             f"{vals_unet[2024]*100:.2f} %", f"**{vals_unet.mean()*100:.2f} % ± {vals_unet.std()*100:.2f} %**"])
T(rows, [6.0, 2.5, 2.5, 2.5, 3.1])

H2("5.4 Costo de cómputo de las 13 corridas")
_tiempo_clf = exp[exp.tarea == "clasificacion"].tiempo_min.sum()
_tiempo_seg = exp[exp.tarea == "segmentacion"].tiempo_min.sum()
_media_clf = exp[exp.tarea == "clasificacion"].tiempo_min.mean()
_media_seg = exp[exp.tarea == "segmentacion"].tiempo_min.mean()
P(f"Los {len(exp)} entrenamientos completos del sprint sumaron "
  f"{exp.tiempo_min.sum():.1f} minutos de GPU (≈{exp.tiempo_min.sum()/60:.1f} horas) en la RTX 5060 Laptop "
  f"de 8 GB: {_tiempo_clf:.1f} min en las 7 corridas de clasificación y {_tiempo_seg:.1f} min en las 6 de "
  f"segmentación — la U-Net tarda, en promedio, {_media_seg/_media_clf:.1f} veces más que el clasificador "
  "por corrida, coherente con que procesa máscara y mapa de salida además de la imagen.")
if (FIGS / "tiempo_entrenamiento.png").exists():
    FIG(FIGS / "tiempo_entrenamiento.png", 15, "Tiempo de entrenamiento de cada una de las 13 filas de "
        "experimentos.csv (columna tiempo_min), coloreado por tarea y etiquetado con arquitectura y el "
        "sufijo de hora del id. Las corridas más largas son las de segmentación con 2 semillas adicionales "
        "(22,0–22,4 min); la más corta es el clasificador con batch=64 (4,1 min), coherente con que un lote "
        "más grande reduce el número de pasos por época.")
page_break()

# ================================================================ 6. R09
H1("6. Riesgo R09 — posible atajo por procedencia de la imagen")
P("El Sprint 1 detectó que el plano de corte, el brillo y el tipo de archivo de origen (gris/RGB) cambian "
  "con la clase (por ejemplo, el 100 % de «sin tumor» es RGB y el 88 % de glioma es gris), lo que podría "
  "dejar que el modelo aprenda un atajo en vez de la señal médica real. Se evaluaron ambos modelos ganadores "
  "desglosados por plano de corte y por tipo de archivo, usando `evaluar_grupos.py` (el desglose de la U-Net "
  "por clase y por plano, con sus propias cifras, ya se presentó en la sección 4.4; aquí se añade el eje de "
  "tipo de archivo, que es el que importa para R09).")
if (FIGS / "r09_desglose.png").exists():
    FIG(FIGS / "r09_desglose.png", 16, "Desglose real de desempeño por tipo de archivo de origen (gris/RGB), "
        "sobre el conjunto de validación.")
B("**Clasificador:** sin diferencias relevantes por plano de corte (98,9 %–99,7 % de accuracy). Por tipo de "
  "archivo: 99,37 % (gris) vs. 99,81 % (RGB). El 100 % de las imágenes «sin tumor» en esta validación son "
  "RGB — confirma el hallazgo del Sprint 1, no es una falla del modelo.")
B("**U-Net:** el glioma es la clase más difícil de segmentar (67,43 % IoU, frente a 90,12 % de meningioma), "
  "como se anticipó por su bajo contraste con el tejido. Hay una brecha de ~8 puntos entre imágenes de "
  "origen gris (76,50 % IoU) y RGB (84,83 % IoU); como el glioma es mayoritariamente en escala de grises, "
  "esta brecha parece explicarse en buena parte por la dificultad propia del glioma y no solo por un atajo "
  "de procedencia — queda como punto de atención para repetir este análisis sobre la prueba oficial en HU12.")
NOTE("Otros riesgos de la sección 9 del traspaso: **R01** (fuga entre pacientes) mitigado con la partición "
     "propia agrupada por `grupo_hash`; **R04** (arquitecturas inestables) mitigado comparando 2 "
     "arquitecturas y repitiendo con 3 semillas; **R06** (memoria de GPU) no se presentó con lote 32–64 "
     "(clasificador) y 8–16 (U-Net) y precisión mixta.")
page_break()

# ================================================================ 7. HU09 TABLA COMPLETA
H1("7. Registro completo de experimentos (HU09)")
P(f"Las {len(exp)} corridas completas del Sprint 2, con su configuración, métrica principal de validación y "
  "tiempo de entrenamiento (detalle completo, incluida la matriz de recall por clase, en "
  "`experimentos.csv`).")
rows = [["id", "Historia", "Tarea", "Config.", "Semilla", "Métrica principal", "Tiempo"]]
for _, r in exp.iterrows():
    if r.tarea == "clasificacion":
        config = f"{r.arquitectura}, lr={r.lr}, batch={r.batch}, aum.={'sí' if r.aumento else 'no'}"
        metrica = f"recall medio {r.recall_medio*100:.2f} %" if pd.notna(r.recall_medio) else "—"
    else:
        config = f"U-Net {r.arquitectura.split('_')[-1]}, lr={r.lr}, batch={r.batch}, aum.={'sí' if r.aumento else 'no'}"
        metrica = f"IoU {r.val_iou*100:.2f} %" if pd.notna(r.val_iou) else "—"
    marca_tiempo = "_".join(r.id.rsplit("_", 2)[-2:])  # AAAAMMDD_HHMMSS, suficiente para distinguir corridas
    rows.append([marca_tiempo, r.historia, r.tarea[:4], config, str(r.semilla), metrica, f"{r.tiempo_min:.1f} min"])
T(rows, [3.6, 1.6, 1.4, 4.8, 1.4, 2.6, 1.2], size=7.8)

H2("Modelos elegidos para el Sprint 3")
B(f"**Clasificación:** EfficientNetB0 (batch=64, lr=3e-4) — {vals_clf.mean()*100:.2f} % de recall medio "
  "promedio en 3 semillas. Se eligió por mejor desempeño promedio y menor tiempo de entrenamiento que ResNet50.")
B(f"**Segmentación:** U-Net ResNet34 (lr=1e-4) — {vals_unet.mean()*100:.2f} % de IoU promedio en 3 semillas. "
  "Se eligió por mejor desempeño promedio frente a la configuración base y a la ablación sin aumento.")
page_break()

# ================================================================ 8. LIMITACIONES Y AMENAZAS A LA VALIDEZ
H1("8. Limitaciones y amenazas a la validez")
P("Ningún número de este informe es falso, pero varios tienen un alcance más chico del que parece a primera "
  "lectura. Esta sección reúne, en un solo lugar, qué tan lejos se puede estirar cada resultado.")
B("**Tamaño de validación:** 1.001 imágenes para el clasificador y 787 con máscara para la U-Net — "
  "suficiente para las metas del acta, pero pequeño frente al tamaño "
  "típico de un estudio clínico; los grupos de la sección 4.4 (de 230 a 291 imágenes por clase, de 249 a "
  "273 por plano) son todavía más chicos, así que una diferencia de 1 o 2 puntos porcentuales entre grupos "
  "puede deberse al azar de qué imágenes cayeron en cada uno.")
B("**La prueba oficial (1.000 imágenes) no se tocó:** ni para elegir arquitectura, ni hiperparámetro, ni "
  "época, ni para este análisis por grupo. Todas las cifras de este informe son de validación; se evaluará "
  "una sola vez en HU12 (Sprint 3), y el Sprint 1 ya advirtió que esa prueba difiere moderadamente del "
  "entrenamiento (más imágenes en gris, otro brillo en algunas clases).")
B(f"**Variabilidad entre semillas:** repetir la configuración ganadora con 3 semillas dio "
  f"{vals_clf.mean()*100:.2f} % ± {vals_clf.std()*100:.2f} % de recall medio (clasificador) y "
  f"{vals_unet.mean()*100:.2f} % ± {vals_unet.std()*100:.2f} % de IoU (U-Net) — sección 5.3. Varias "
  "diferencias de HU08 son del mismo orden que esa variación: la U-Net con `batch=16` midió 80,09 % de IoU "
  "a una sola semilla, apenas por encima del 79,78 % de la configuración `lr=1e-4` elegida (que sí tiene 3 "
  "semillas); no se puede afirmar con esta evidencia que `batch=16` sea realmente mejor.")
B("**Desglose por grupo en una sola semilla:** el análisis por clase, plano y tipo de archivo (secciones 4.4 "
  "y 6) se hizo sobre el checkpoint de semilla 42 únicamente, no promediado sobre las 3 semillas del modelo "
  "final; repetirlo con las otras 2 semillas podría mover un poco las cifras de cada grupo, aunque es poco "
  "probable que cambie cuál clase es la más difícil.")
B("**El hallazgo de R09 queda sin resolver del todo:** la brecha de ~8 puntos de IoU entre imágenes en "
  "escala de grises y RGB (sección 6) está mezclada con el hecho de que el glioma —la clase más difícil— es "
  "mayoritariamente en escala de grises (88 %, Sprint 1). Con los datos de este sprint no se puede separar "
  "cuánto de la brecha es un atajo real de procedencia y cuánto es solo la dificultad propia del glioma; "
  "haría falta, por ejemplo, comparar glioma en gris contra glioma en RGB específicamente, con más imágenes "
  "de las que hay disponibles en esta validación.")
B("**Sin prueba de significancia estadística:** las comparaciones de HU08, de arquitecturas y de R09 son "
  "diferencias de promedios y desvíos descriptivos, no pruebas de hipótesis formales; con 2 o 3 semillas no "
  "alcanza para calcular una con sentido.")
B("**Alcance del dataset:** BRISC 2025 es un conjunto público ya curado, de un solo tipo de secuencia (T1 "
  "con contraste); no se probó con otro dataset, otro escáner ni otra secuencia, así que el desempeño medido "
  "aquí no dice nada sobre qué tan bien generalizaría el modelo a resonancias de otra procedencia.")
B("**La U-Net nunca predice «sin tumor»:** al entrenarse solo con imágenes que tienen máscara, el modelo de "
  "segmentación no se evalúa prediciendo la ausencia de tumor; ese caso lo cubre únicamente el clasificador, "
  "y un sistema real tendría que combinar ambas salidas con cuidado.")

# ================================================================ 9. CONCLUSIONES Y PROXIMOS PASOS
H1("9. Conclusiones y próximos pasos")
H2("9.1 Conclusiones")
B("El pipeline de entrenamiento completo (datos, modelos, métricas, registro de experimentos) quedó "
  "funcionando y es reproducible: semilla fija, configuración y checkpoint guardados, comandos documentados.")
B("Ambos modelos superan las metas del acta de constitución medidas sobre validación.")
B("El ajuste de hiperparámetros (HU08) mostró que el aumento de datos es lo que más aporta; afinar "
  "learning rate y batch trae mejoras menores a 1 punto porcentual sobre esta base.")
B("El riesgo R09 se investigó con datos reales: no hay evidencia fuerte de un atajo puro en el clasificador; "
  "en la U-Net, la brecha gris/RGB coincide con la dificultad conocida del glioma, pero merece seguimiento "
  "en la prueba oficial (HU12).")

H2("9.2 Qué sigue (Sprint 3, 24–30 oct 2026)")
B("**HU12:** evaluación única sobre la prueba oficial (1.000 imágenes), incluyendo el desglose por plano y "
  "tipo de archivo ya preparado en `evaluar_grupos.py`.")
B("**HU13:** aplicación web de demostración con el modelo exportado (ONNX, riesgo R05 de tamaño en navegador).")
B("**HU14:** MLOps básico — versionado de modelos y registro de métricas.")
B("**HU15–HU16:** informe final y exposición.")

H2("9.3 Qué no cubre este informe (gestión del equipo)")
P("Por fuera de lo técnico, el Sprint 2 todavía necesita (ver sección 15.1 del traspaso, a cargo del "
  "equipo, no de este informe): el Backlog del Sprint 2 en Trello/Excel con tareas y responsables reales, "
  "el Informe de Estado y la Minuta de Reunión actualizados, el Registro de Riesgos con R09 agregado, la "
  "Retrospectiva del Sprint 2 (hecha con el equipo, no por una herramienta), y la presentación del Sprint 2 "
  "(HU10) del 23 de octubre.")
page_break()

# ================================================================ 10. GLOSARIO
H1("10. Glosario mínimo")
P("Basado en la sección 14 de `docs/TRASPASO_SPRINT2.md`, con los términos técnicos adicionales que usa "
  "este informe.", italic=True, size=9.5, color=GRAY)
B("**HU:** historia de usuario, la unidad de trabajo de Scrum (por ejemplo, HU06 es «entrenar el "
  "clasificador»).")
B("**EDA:** análisis exploratorio de datos — lo que hizo el Sprint 1 antes de entrenar ningún modelo.")
B("**CRISP-ML(Q):** ciclo de vida de un proyecto de aprendizaje automático con un paso de calidad en cada "
  "fase (requisitos y restricciones, riesgos, selección de modelos documentada, reproducibilidad).")
B("**Clasificación:** decir qué tipo de tumor hay en la imagen, una de 4 clases. **Segmentación:** marcar "
  "en qué píxeles de la imagen está el tumor.")
B("**IoU (*Intersection over Union*):** el área donde la máscara predicha y la real coinciden, dividida "
  "entre el área que ocupan entre las dos juntas; 100 % es una coincidencia perfecta, 0 % ninguna.")
B("**Dice:** mide lo mismo que el IoU (el solapamiento entre máscara predicha y real), pero con una fórmula "
  "que da más peso al área que sí coincide; por eso el Dice de una misma predicción siempre es igual o mayor "
  "que su IoU.")
B("**Recall:** de los casos reales de una clase, qué porcentaje detecta el modelo (por ejemplo, de los "
  "gliomas reales en validación, cuántos el modelo etiquetó como glioma).")
B("**F1 macro:** promedio del equilibrio entre precisión y recall de cada clase, calculado por igual para "
  "las 4 clases sin importar cuántas imágenes tenga cada una.")
B("**Transfer learning:** partir de una red ya entrenada con otro conjunto de datos (aquí, ImageNet) en vez "
  "de empezar con pesos al azar, para aprovechar lo que esa red ya «sabe» sobre bordes, texturas y formas.")
B("**Fuga (*data leakage*):** que imágenes casi idénticas caigan en el entrenamiento y en el conjunto que "
  "se usa para medir el resultado, lo que infla la métrica sin que el modelo generalice mejor de verdad.")
B("**Ablación:** quitar o cambiar una sola parte de la configuración (por ejemplo, el aumento de datos) "
  "manteniendo todo lo demás igual, para medir cuánto aporta esa parte por sí sola.")
B("**Aumento de datos:** transformaciones aleatorias (giro, rotación, cambios de brillo) aplicadas a cada "
  "imagen durante el entrenamiento, para que el modelo vea más variedad sin recolectar más datos.")
B("**Época y lote (*batch*):** una época es una pasada completa por todas las imágenes de entrenamiento; "
  "el lote es cuántas imágenes ve el modelo antes de actualizar sus pesos una sola vez.")
B("**Precisión mixta:** usar números de menor precisión en parte del cálculo para entrenar más rápido en la "
  "GPU, sin cambiar la arquitectura ni, en la práctica, el resultado final.")
B("**Parada temprana:** detener el entrenamiento si la métrica de validación deja de mejorar durante varias "
  "épocas seguidas, para no sobreajustar ni gastar más tiempo de GPU del necesario.")
B("**Checkpoint:** el archivo con los pesos del modelo guardados en su mejor época de validación.")
B("**Semilla:** el número que fija el generador de números aleatorios del entrenamiento, para poder repetir "
  "una corrida exactamente o para medir cuánto cambia el resultado si solo se cambia ese número.")

d.save(OUT)
print("Informe guardado en:", OUT)
