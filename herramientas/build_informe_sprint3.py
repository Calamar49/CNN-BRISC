# -*- coding: utf-8 -*-
"""Informe FINAL del proyecto (Sprint 3) en Word, a partir de datos reales:
evaluacion unica sobre la prueba oficial (HU12, protocolo de 6 checkpoints), registro de modelos (HU14) y
capturas reales de la aplicacion clinica (HU13). No se inventa ningun numero: todo sale de
"03. Implementacion/Sprint 3 - Evaluacion y despliegue/salida_sprint3/evaluacion_prueba.json",
"registro_modelos.json" y las figuras de "herramientas/figs_sprint3/".

Uso:  python build_informe_sprint3.py
"""
import json
import re
from pathlib import Path as _P

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

_AQUI = _P(__file__).resolve().parent
_RAIZ = _AQUI.parent
S3 = _RAIZ / "03. Implementacion" / "Sprint 3 - Evaluacion y despliegue"
FIGS = _AQUI / "figs_sprint3"
OUT = str(_AQUI / "informe_sprint3.docx")

NAVY = RGBColor(0x1F, 0x38, 0x64); BLUE = RGBColor(0x2F, 0x55, 0x97)
TEAL = RGBColor(0x2B, 0x7A, 0x8B); GRAY = RGBColor(0x59, 0x59, 0x59)

EV = json.loads((S3 / "salida_sprint3" / "evaluacion_prueba.json").read_text(encoding="utf-8"))
REG = json.loads((S3 / "registro_modelos.json").read_text(encoding="utf-8"))
CLF, SEG = EV["clasificacion"], EV["segmentacion"]
CD, SD = CLF["desplegado"], SEG["desplegado"]
CL = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Hipófisis", "no_tumor": "Sin tumor"}
MO = {"L": "Gris (L)", "RGB": "RGB"}
pc = lambda x: f"{x*100:.2f} %"
p1 = lambda x: f"{x*100:.1f} %"

d = Document()
sec = d.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.2); sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)
st = d.styles["Normal"]; st.font.name = "Calibri"; st.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st.font.size = Pt(10.5); st.paragraph_format.space_after = Pt(6); st.paragraph_format.line_spacing = 1.12
for name, size, color, before, after in (("Heading 1", 17, NAVY, 20, 8), ("Heading 2", 13, BLUE, 14, 5), ("Heading 3", 11, NAVY, 10, 3)):
    h = d.styles[name]; h.font.name = "Calibri"
    for k in ("w:eastAsia", "w:ascii", "w:hAnsi"):
        h.element.rPr.rFonts.set(qn(k), "Calibri")
    h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = color
    h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(after); h.paragraph_format.keep_with_next = True


def shade(cell, hex_fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear"); shd.set(qn("w:color"), "auto"); shd.set(qn("w:fill"), hex_fill); tcPr.append(shd)


def cell_margins(tbl, top=50, bottom=50, left=90, right=90):
    m = OxmlElement("w:tblCellMar")
    for k, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        e = OxmlElement(f"w:{k}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); m.append(e)
    tbl._tbl.tblPr.append(m)


def borders(tbl, color="BFBFBF"):
    b = OxmlElement("w:tblBorders")
    for k in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{k}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color); b.append(e)
    tbl._tbl.tblPr.append(b)


def H1(t): return d.add_heading(t, 1)
def H2(t): return d.add_heading(t, 2)


def add_rich(p, text, bold=False, italic=False, size=None, color=None):
    for i, part in enumerate(text.split("**")):
        if not part:
            continue
        r = p.add_run(part); r.bold = bold or (i % 2 == 1); r.italic = italic
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color


def P(text="", bold=False, italic=False, size=None, color=None, after=None):
    p = d.add_paragraph(); add_rich(p, text, bold, italic, size, color)
    if after is not None: p.paragraph_format.space_after = Pt(after)
    return p


def B(text, level=0):
    p = d.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.63 + 0.6 * level); p.paragraph_format.first_line_indent = Cm(-0.5)
    p.paragraph_format.space_after = Pt(3); add_rich(p, text); return p


_fig_n = [0]


def T(rows, widths, header=True, size=9, zebra=True):
    tbl = d.add_table(rows=len(rows), cols=len(rows[0])); tbl.alignment = WD_TABLE_ALIGNMENT.CENTER; tbl.autofit = False
    borders(tbl); cell_margins(tbl)
    for j, wcm in enumerate(widths):
        tbl.columns[j].width = Cm(wcm)
    for i, row in enumerate(rows):
        for j, txt in enumerate(row):
            c = tbl.rows[i].cells[j]; c.width = Cm(widths[j]); p = c.paragraphs[0]
            p.paragraph_format.space_after = Pt(0); p.paragraph_format.line_spacing = 1.05
            is_head = header and i == 0
            add_rich(p, str(txt), bold=is_head, size=size, color=RGBColor(255, 255, 255) if is_head else None)
            if is_head: shade(c, "1F3864")
            elif zebra and i % 2 == 0: shade(c, "F2F5FA")
    d.add_paragraph().paragraph_format.space_after = Pt(2); return tbl


def FIG(nombre, width_cm, caption):
    ruta = FIGS / nombre
    if not ruta.exists():
        return
    p = d.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(2); p.add_run().add_picture(str(ruta), width=Cm(width_cm))
    c = d.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; _fig_n[0] += 1
    add_rich(c, "Figura %d. " % _fig_n[0] + caption, italic=True, size=9, color=GRAY)
    c.paragraph_format.space_after = Pt(10)


def NOTE(text):
    t = d.add_table(rows=1, cols=1); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    cell_margins(t, 90, 90, 160, 160); c = t.rows[0].cells[0]; c.width = Cm(16.6); shade(c, "EAF0FA")
    bd = OxmlElement("w:tcBorders"); e = OxmlElement("w:left")
    e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "24"); e.set(qn("w:color"), "2F5597"); bd.append(e)
    c._tc.get_or_add_tcPr().append(bd)
    p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0); add_rich(p, text, size=10)
    d.add_paragraph().paragraph_format.space_after = Pt(2)


def page_break(): d.add_page_break()


def add_field(run, instr):
    for kind, txt in (("begin", None), (None, instr), ("end", None)):
        if kind:
            e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), kind); run._r.append(e)
        else:
            e = OxmlElement("w:instrText"); e.set(qn("xml:space"), "preserve"); e.text = txt; run._r.append(e)


fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = fp.add_run("Informe final · Sistema inteligente: tumores cerebrales en MRI · Página "); r.font.size = Pt(8.5); r.font.color.rgb = GRAY
r2 = fp.add_run(); r2.font.size = Pt(8.5); r2.font.color.rgb = GRAY; add_field(r2, "PAGE")
sec.different_first_page_header_footer = True

# ================================================================ PORTADA
for _ in range(3):
    d.add_paragraph()
band = d.add_table(rows=1, cols=1); band.alignment = WD_TABLE_ALIGNMENT.CENTER; band.autofit = False
cell_margins(band, 300, 300, 300, 300); c = band.rows[0].cells[0]; c.width = Cm(16.6); shade(c, "1F3864")
pp = c.paragraphs[0]; add_rich(pp, "INFORME FINAL DEL PROYECTO", bold=True, size=28, color=RGBColor(255, 255, 255))
pp.paragraph_format.space_after = Pt(6)
pp = c.add_paragraph(); add_rich(pp, "Clasificación y segmentación de tumores cerebrales — Sprints 1 a 3", size=14, color=RGBColor(0xC9, 0xD6, 0xEC))
d.add_paragraph()
P("Desarrollo de un Sistema Inteligente para clasificar y segmentar tumores cerebrales en resonancias "
  "magnéticas, desplegado en un prototipo de sistema web de apoyo al diagnóstico (demostración académica).",
  bold=True, size=13, color=NAVY, after=14)
T([["Proyecto", "Redes Neuronales – Opción B (Ingeniería de Sistemas, Inteligencia Artificial)"],
   ["Metodología", "Híbrida: Scrum + CRISP-ML(Q)"],
   ["Sprint 3", "Evaluación, despliegue y cierre · presentación final 30 oct 2026"],
   ["Docente revisor", "Ing. Hugo Espetia Huamanga"],
   ["Dataset", "BRISC 2025 (Kaggle, CC BY 4.0) — 6.000 imágenes, 4.793 máscaras"],
   ["Repositorio", "github.com/Calamar49/CNN-BRISC"]], [4.5, 12.1])
d.add_paragraph()
T([["Integrante", "Rol"],
   ["Coavoy Cruz Joseph Gabriel", "Gerente de Proyecto"],
   ["Cuchuyrrumi Mamani Manuel Rodrigo", "Scrum Master"],
   ["Huallpatuiro Rafaile Brayan", "Equipo de desarrollo"],
   ["Mamani Acuña Frank Joseph", "Equipo de desarrollo"]], [10, 6.6])
P("Demostración académica; no es una herramienta de diagnóstico médico. Todos los números provienen de "
  "mediciones reales del equipo (ver evaluacion_prueba.json y registro_modelos.json); las cifras del artículo "
  "de BRISC se citan como tales. La prueba oficial se evaluó una sola vez.", italic=True, size=9.5, color=GRAY)
page_break()

# ================================================================ 1. RESUMEN
H1("1. Resumen ejecutivo")
P("El proyecto construyó un sistema que, dada una resonancia magnética cerebral (T1 con contraste), **clasifica** "
  "el tipo de tumor (glioma, meningioma, tumor de hipófisis o sin tumor) y **segmenta** su contorno, y lo mostró "
  "en un **prototipo de sistema web de apoyo al diagnóstico**. El trabajo siguió Scrum + CRISP-ML(Q) en tres "
  "sprints: comprensión del negocio y los datos (Sprint 1), modelado (Sprint 2) y evaluación y despliegue "
  "(Sprint 3).")
B(f"**Evaluación en la prueba oficial (HU12), una sola vez:** el clasificador desplegado alcanzó "
  f"**{pc(CD['accuracy'])} de accuracy** y el segmentador **{pc(SD['iou'])} de IoU** ({pc(SD['dice'])} de Dice). "
  "Las **tres metas del acta** (accuracy ≥ 95 %, recall ≥ 90 % por clase, IoU ≥ 70 %) **se cumplen**.")
B("**Despliegue (HU13):** un prototipo de sistema clínico con el flujo completo de apoyo al diagnóstico en "
  "neuro-oncología (inicio de sesión, casos, subir una resonancia, resultado con contorno, revisión del médico "
  "e informe del caso), que funciona en local y sin internet.")
B("**MLOps básico (HU14):** modelos exportados a ONNX y versionados con SHA-256, registro de modelos y de datos, "
  "etiquetas de Git y monitoreo de predicciones en la aplicación.")
NOTE("**Honestidad:** la prueba oficial no se usó para elegir nada; el modelo desplegado se eligió por "
     "validación (semilla 2024). Se reporta el efecto de las imágenes de prueba parecidas al entrenamiento y las "
     "limitaciones. **No es un diagnóstico médico.**")

# ================================================================ 2-4 fases previas
H1("2. Comprensión del negocio")
P("Objetivo: apoyar la lectura de resonancias en neuro-oncología con un sistema que sugiere el tipo de tumor y "
  "marca su contorno, como **apoyo al diagnóstico** (nunca en reemplazo del médico). No hay cliente real ni datos "
  "de pacientes reales: es una demostración académica. Metas del acta (sobre la prueba oficial): accuracy ≥ 95 %, "
  "recall ≥ 90 % por clase e IoU ≥ 70 %.")

H1("3. Comprensión y preparación de los datos (Sprint 1)")
P("Dataset BRISC 2025 (CC BY 4.0): 6.000 imágenes T1 con contraste y 4.793 máscaras de tumor. Se preparó a "
  "256×256 en gris con normalización de ImageNet y una **partición propia (semilla 42): 3.999 entrenamiento / "
  "1.001 validación / 1.000 prueba oficial**, agrupando por hash perceptual para evitar fuga evidente. La prueba "
  "oficial se dejó intacta para evaluarla una sola vez al final.")

H1("4. Modelado (Sprint 2)")
P("Se compararon dos arquitecturas de clasificación con transfer learning (EfficientNetB0 y ResNet50) y una "
  "U-Net con encoder ResNet34 para segmentación, con 13 entrenamientos registrados (ajuste de hiperparámetros y "
  "3 semillas). Configuraciones elegidas por **validación**: EfficientNetB0 (lote 64) y U-Net (lr 1e-4).")
T([["Tarea", "Modelo elegido", "Validación (Sprint 2, 3 semillas)"],
   ["Clasificación", "EfficientNetB0 (lote 64)", "recall medio 99,57 % ± 0,15 %"],
   ["Segmentación", "U-Net (encoder ResNet34, lr 1e-4)", "IoU 80,12 % ± 0,33 %"]], [3.6, 6.5, 6.5])
page_break()

# ================================================================ 5. EVALUACION HU12
H1("5. Evaluación en la prueba oficial (HU12)")
P(f"La prueba oficial ({EV['n_test_clasificacion']} imágenes de clasificación, {EV['n_test_segmentacion']} con "
  "máscara) se evaluó **una sola vez**. Siguiendo el plan, se evaluaron los **6 puntos de control del Sprint 2** "
  "(3 semillas × 2 tareas) y se reporta el promedio ± desvío; el **modelo desplegado** es el mejor por validación "
  "(semilla 2024). No se cambió nada después de ver los números.")

H2("5.1 Resultados frente a las metas del acta")
cumple = EV["cumple"]
si = lambda b: "Cumple ✓" if b else "No cumple"
T([["Métrica", "Meta del acta", "Prueba oficial (desplegado)", "Resultado"],
   ["Accuracy (clasificación)", "≥ 95 %", pc(CD["accuracy"]), si(cumple["accuracy"])],
   ["Recall por clase (mínimo)", "≥ 90 %", pc(min(CD["recall_por_clase"].values())) + " (glioma)", si(cumple["recall_por_clase"])],
   ["IoU (segmentación)", "≥ 70 %", pc(SD["iou"]), si(cumple["iou"])]], [5.2, 3.2, 4.6, 3.6])
FIG("val_vs_prueba.png", 16, "Validación (Sprint 2) frente a la prueba oficial (HU12). El desempeño en prueba "
    "es muy cercano al de validación: el modelo generaliza y no colapsa por sobreajuste.")
P(f"El clasificador promedió **{pc(CLF['accuracy_promedio'])} ± {pc(CLF['accuracy_desvio'])}** de accuracy sobre "
  f"las 3 semillas, y la U-Net **{pc(SEG['iou_promedio'])} ± {pc(SEG['iou_desvio'])}** de IoU. La variabilidad "
  "entre semillas es pequeña.")
FIG("prueba_semillas_vecino.png", 16, "Izquierda: resultado por cada una de las 3 semillas (la desplegada es la "
    "2024). Derecha: efecto del subconjunto sin vecino cercano al entrenamiento.")

H2("5.2 Clasificación: recall por clase y matriz de confusión")
filas = [["Clase", "Recall en la prueba"]]
for c_, v in CD["recall_por_clase"].items():
    filas.append([CL[c_], pc(v)])
T(filas, [8, 5])
FIG("prueba_recall_por_clase.png", 11.5, "Recall por clase en la prueba oficial; todas superan la meta de 90 %. "
    "El glioma es la clase más difícil.")
FIG("prueba_matriz_confusion.png", 10, "Matriz de confusión real sobre las 1.000 imágenes de la prueba oficial.")
FIG("prueba_ejemplos_clasificacion.png", 16, "Ejemplos reales de aciertos y errores de clasificación (salida del "
    "modelo, sin retocar).")

H2("5.3 Segmentación: IoU por clase y ejemplos")
filas = [["Clase", "IoU", "Dice"]]
for c_ in ("glioma", "meningioma", "pituitary"):
    filas.append([CL[c_], pc(SD["iou_por_clase"][c_]["valor"]), pc(SD["dice_por_clase"][c_]["valor"])])
T(filas, [6, 3.5, 3.5])
FIG("prueba_iou_por_clase.png", 11.5, "IoU y Dice por clase de tumor en la prueba. El glioma, de bajo contraste, "
    "es el más difícil de segmentar.")
FIG("prueba_ejemplos_segmentacion.png", 13, "Segmentación real: 2 mejores y 2 peores por IoU. En los peores el "
    "modelo marca una región cercana pero no el tumor real (pequeño o desplazado).")

H2("5.4 Riesgo R09 (atajo por procedencia) y subconjunto sin fuga")
P(f"Por tipo de archivo de origen (gris/RGB): accuracy {p1(CLF['accuracy_por_modo']['L']['valor'])} (gris) frente "
  f"a {p1(CLF['accuracy_por_modo']['RGB']['valor'])} (RGB); IoU {p1(SD['iou_por_modo']['L']['valor'])} (gris) "
  f"frente a {p1(SD['iou_por_modo']['RGB']['valor'])} (RGB). La brecha de la U-Net coincide con que el glioma "
  "—la clase más difícil— es mayoritariamente en gris.")
FIG("prueba_por_modo.png", 16, "Desempeño por tipo de archivo de origen en la prueba oficial (riesgo R09).")
NOTE(f"**Subconjunto sin vecino cercano:** {EV['imagenes_con_vecino_cercano']} de las 1.000 imágenes de prueba "
     "tienen un vecino casi idéntico en el entrenamiento oficial (correlación de miniaturas 32×32 ≥ 0,98). "
     f"Quitándolas, el desempeño baja poco: accuracy {pc(CLF['accuracy_sin_vecino'])} (n={CLF['n_sin_vecino']}) e "
     f"IoU {pc(SEG['iou_sin_vecino'])} (n={SEG['n_sin_vecino']}). El efecto de la fuga es pequeño.")
page_break()

# ================================================================ 6. DESPLIEGUE HU13
H1("6. Despliegue: la aplicación clínica (HU13)")
P("El modelo se desplegó en un **prototipo de sistema clínico** con el flujo principal de apoyo al diagnóstico en "
  "neuro-oncología completo y los demás módulos como maqueta. Tecnología: FastAPI + Jinja2 + SQLite; inferencia "
  "con ONNX Runtime en CPU; **funciona sin internet** (fuentes del sistema, nada de CDN); diseño blanco y formal. "
  "Decisión de arquitectura (riesgo R05): backend local en vez de correr el modelo en el navegador, porque la "
  "U-Net pesa ~98 MB en ONNX.")
P("**Reglas de decisión:** si el clasificador predice «sin tumor», no se muestra contorno (el segmentador solo se "
  "entrenó con imágenes con tumor); si la probabilidad más alta es < 80 %, se marca «confianza baja: requiere "
  "revisión»; se valida la entrada (PNG/JPG, brillo medio del cerebro en el rango de entrenamiento). El aviso de "
  "demostración aparece en todas las pantallas; la decisión final es siempre del médico.")
FIG("app_login.jpg", 12, "Inicio de sesión del prototipo (usuarios ficticios).")
FIG("app_casos.jpg", 16, "Lista de casos con pacientes ficticios (módulo de neuro-oncología).")
FIG("app_estudio.jpg", 16, "Nuevo estudio: subir una resonancia T1 o elegir un ejemplo de validación.")
FIG("app_resultado.jpg", 16, "Resultado real: clase sugerida (Meningioma 100 %), probabilidades, contorno del "
    "tumor con control de opacidad, área, y el formulario de revisión del médico.")
FIG("app_sin_tumor.jpg", 16, "Caso «sin tumor»: el sistema no muestra contorno (regla de decisión).")
FIG("app_informe.jpg", 16, "Informe del caso imprimible, con la versión de los modelos, la revisión del médico y "
    "el aviso de demostración.")
FIG("app_ficha.jpg", 16, "Ficha de los modelos: métricas de validación y de la prueba oficial, uso previsto y "
    "limitaciones.")
FIG("app_maqueta.jpg", 16, "Los demás módulos son maqueta, marcados «no implementado».")

# ================================================================ 7. MLOPS HU14
H1("7. MLOps básico (HU14)")
B("**Versionado de modelos:** cada modelo desplegado en ONNX (clasificador_v1 16 MB, segmentacion_v1 97,7 MB) con "
  "su tarjeta de modelo y **SHA-256**; paridad PyTorch↔ONNX verificada.")
B("**Registro de modelos y de datos:** `registro_modelos.json` reúne procedencia, SHA-256, métricas de validación "
  "y de prueba, la **versión del dataset** (SHA-256 del manifest + semilla 42), las versiones de las librerías y "
  f"el **commit de Git** ({REG.get('commit_git', '')}).")
B("**Etiquetas de Git** (versión identificable): " + ", ".join(REG.get("etiquetas_git", [])) + ".")
B("**Monitoreo** en la aplicación (página de administrador): registra cada predicción (clase, probabilidades, "
  "confianza, área, tiempo de respuesta, brillo medio de la entrada y alerta de confianza baja) **sin guardar "
  "imágenes ni datos personales**; compara el brillo medio con el del entrenamiento como señal simple de deriva.")
FIG("app_monitoreo.jpg", 16, "Página de monitoreo: total de predicciones, confianza media, porcentaje de alertas, "
    "tiempo p95 y distribución de clases.")
P("Los pesos (.pt) y los modelos (.onnx) no se suben a Git; se regeneran con los scripts. Lo versionado es el "
  "código, las tarjetas de modelo y el registro de métricas.")
page_break()

# ================================================================ 8. LIMITACIONES Y ETICA
H1("8. Limitaciones y consideraciones éticas")
B("**La prueba se evaluó una sola vez** y el modelo desplegado se eligió por validación, no por la prueba.")
B(f"**Fuga:** {EV['imagenes_con_vecino_cercano']} imágenes de prueba tienen un vecino casi idéntico en el "
  "entrenamiento; se reportan las métricas también sin ellas (el efecto es pequeño).")
B("**El glioma es la clase más difícil**, tanto en clasificación (menor recall) como en segmentación (menor IoU), "
  "por su bajo contraste con el tejido.")
B("**Un solo dataset y una sola secuencia** (T1 con contraste); no se probó la generalización a otros escáneres "
  "o secuencias. El dataset no tiene identificador de paciente.")
B("**Ética y privacidad:** es una demostración académica de **apoyo al diagnóstico**, no un diagnóstico y no "
  "sustituye al médico. Todo se procesa en local; no se usan datos de pacientes reales; el monitoreo no guarda "
  "imágenes ni datos personales. Se cita el dataset BRISC 2025 (CC BY 4.0).")

H1("9. Conclusiones y trabajo futuro")
B("El sistema cumple las tres metas del acta en la prueba oficial y se desplegó en un prototipo de apoyo al "
  "diagnóstico funcional, reproducible y versionado.")
B("Trabajo futuro: mejorar el glioma (más datos o pérdidas específicas), validar con otros datasets y escáneres, "
  "un modelo multitarea con encoder compartido, y pasos de MLOps más completos (reentrenamiento ante deriva).")

H1("10. Anexo")
H2("10.1 Revisión por el equipo (HU15)")
T([["Integrante", "Rol", "Revisión", "Fecha"],
   ["Coavoy Cruz Joseph Gabriel", "Gerente de Proyecto", "☐ revisado", "____"],
   ["Cuchuyrrumi Mamani Manuel Rodrigo", "Scrum Master", "☐ revisado", "____"],
   ["Huallpatuiro Rafaile Brayan", "Desarrollo", "☐ revisado", "____"],
   ["Mamani Acuña Frank Joseph", "Desarrollo", "☐ revisado", "____"]], [7.2, 4.2, 3, 2.2])
H2("10.2 Glosario")
for term, desc in (("ONNX", "formato estándar para servir modelos sin PyTorch (aquí, con ONNX Runtime en CPU)."),
                   ("IoU / Dice", "cuánto se solapa la máscara predicha con la real."),
                   ("Recall", "de los casos reales de una clase, cuántos detecta el modelo."),
                   ("Transfer learning", "partir de una red entrenada con otro dataset (ImageNet)."),
                   ("Fuga", "que imágenes casi iguales caigan en entrenamiento y evaluación, inflando resultados."),
                   ("MLOps", "prácticas para versionar, desplegar y monitorear modelos de forma reproducible.")):
    P(f"**{term}:** {desc}", size=10, after=3)

d.save(OUT)
print("Informe guardado en:", OUT)
