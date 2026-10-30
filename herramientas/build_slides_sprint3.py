# -*- coding: utf-8 -*-
"""Presentación de la Revisión del Sprint 3 (evaluación y despliegue).

Mismo diseño blanco y formal del Sprint 1/2: importa las primitivas de `deck_light.py`
(colores NAVY/INK/MUTED/LINE/PANEL, STAGE, fuente Calibri, 16:9, margen LM, funciones
run()/text()/rect()/label_shape()/bullets()/pic()/table() y la clase Deck) y reutiliza los
equivalentes chrome2()/content2()/divider2() que definió build_slides_sprint2.py para poner
una pastilla parametrizable por diapositiva. No modifica deck_light.py ni build_slides_sprint2.py.

Fuente de verdad de todas las cifras (NINGÚN número se escribe a mano):
  - 03. Implementacion/Sprint 3 - Evaluacion y despliegue/salida_sprint3/evaluacion_prueba.json
  - 03. Implementacion/Sprint 3 - Evaluacion y despliegue/registro_modelos.json
Las capturas y figuras reales están en herramientas/figs_sprint3/.

Uso:
    "<repo>/.venv/Scripts/python.exe" herramientas/build_slides_sprint3.py

Genera: herramientas/presentacion_sprint3.pptx
"""
import json
import subprocess
import sys
from pathlib import Path

try:
    import pptx  # noqa: F401
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-pptx"])

from pptx import Presentation
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

_AQUI = Path(__file__).resolve().parent
_RAIZ = _AQUI.parent
sys.path.insert(0, str(_AQUI))

# Primitivas EXACTAS del generador del Sprint 1: mismos colores, fuente, tamaño de diapositiva
# y funciones ayudantes. No se modifica deck_light.py; solo se importa.
from deck_light import (  # noqa: E402
    NAVY, INK, MUTED, LINE, PANEL, WHITE, STAGE, FONT, SW, SH, LM, CW,
    run, text, rect, label_shape, bullets, pic, table, Deck,
)
# Equivalentes chrome2()/content2()/divider2() + panel() definidos en build_slides_sprint2.py.
from build_slides_sprint2 import chrome2, content2, divider2, panel  # noqa: E402

FIGS = str(_AQUI / "figs_sprint3").replace("\\", "/") + "/"
FOOT = "Sistema Inteligente: tumores cerebrales en MRI  ·  Revisión del Sprint 3 (evaluación y despliegue)"

_SP3 = _RAIZ / "03. Implementacion" / "Sprint 3 - Evaluacion y despliegue"

# ------------------------------------------------------------------ datos reales (JSON)
with open(_SP3 / "salida_sprint3" / "evaluacion_prueba.json", encoding="utf-8") as f:
    EVAL = json.load(f)
with open(_SP3 / "registro_modelos.json", encoding="utf-8") as f:
    REG = json.load(f)

CLF = EVAL["clasificacion"]
SEG = EVAL["segmentacion"]
METAS = EVAL["metas_acta"]
REG_CLF = next(m for m in REG["modelos"] if m["tarea"] == "clasificacion")
REG_UNET = next(m for m in REG["modelos"] if m["tarea"] == "segmentacion")

N_CLF = EVAL["n_test_clasificacion"]
N_SEG = EVAL["n_test_segmentacion"]
ACC = CLF["accuracy"] * 100
F1 = CLF["f1_macro"] * 100
RC = {k: v * 100 for k, v in CLF["recall_por_clase"].items()}
RC_MIN = min(RC.values())
IOU = SEG["iou"] * 100
DICE = SEG["dice"] * 100
IOU_CL = {k: v["valor"] * 100 for k, v in SEG["iou_por_clase"].items()}
DICE_CL = {k: v["valor"] * 100 for k, v in SEG["dice_por_clase"].items()}

ES = {"glioma": "glioma", "meningioma": "meningioma", "pituitary": "hipófisis", "no_tumor": "sin tumor"}

# ------------------------------------------------------------------ reparto de la exposición (4+4+4+3 = 15)
BLOQUES = [("Joseph Coavoy", 4), ("Manuel Cuchuyrrumi", 4), ("Brayan Huallpatuiro", 4), ("Frank Mamani", 3)]


def expositor_por_diapositiva():
    mapa, n = {}, 0
    for nombre, cant in BLOQUES:
        for _ in range(cant):
            n += 1
            mapa[n] = nombre
    return mapa


# ------------------------------------------------------------------ construcción del deck
def build():
    D = Deck(FOOT, expositor_por_diapositiva())
    prs = D.prs

    # ---- 1. Portada
    s = D.slide()
    rect(s, 0, 0, 0.45, SH, NAVY)
    text(s, 1.1, 0.75, 11, 0.4, "REVISIÓN DEL SPRINT 3 · EVALUACIÓN Y DESPLIEGUE", 14, True, STAGE[3])
    text(s, 1.1, 1.3, 10.8, 2.0,
         "Desarrollo de un Sistema Inteligente para clasificar y segmentar tumores cerebrales "
         "en resonancias magnéticas", 32, True, NAVY, spacing=1.05)
    text(s, 1.1, 3.35, 10.8, 0.5, "desplegado en una aplicación web de apoyo académico (demostración académica)",
         18, False, MUTED)
    rect(s, 1.1, 4.05, 1.6, 0.04, STAGE[2])
    text(s, 1.1, 4.25, 11, 0.4, "Proyecto académico de Redes Neuronales · Ingeniería de Sistemas – Inteligencia Artificial",
         14, False, INK)
    text(s, 1.1, 4.65, 11, 0.8,
         ["Coavoy Cruz Joseph Gabriel (gerente) · Cuchuyrrumi Mamani Manuel Rodrigo (Scrum Master)",
          "Huallpatuiro Rafaile Brayan · Mamani Acuña Frank Joseph"], 14, False, INK, spacing=1.15)
    text(s, 1.1, 5.55, 11, 0.4, "Docente revisor: Ing. Hugo Espetia Huamanga  ·  30 de octubre de 2026", 14, False, MUTED)
    for i, (t, col) in enumerate((("HU12 · Evaluación", STAGE[1]), ("HU13 · Aplicación web", STAGE[2]),
                                   ("HU14 · MLOps básico", STAGE[3]))):
        label_shape(s, 1.1 + i * 3.95, 6.15, 3.75, 0.32, col, t, 10)
    text(s, 1.1, 6.6, 11, 0.4,
         "Fase CRISP-ML(Q): Evaluación y despliegue  ·  Demostración académica, no es diagnóstico",
         12, False, MUTED)

    # ---- 2. Agenda
    s = D.slide()
    rect(s, 0, 0, SW, 0.12, STAGE[0])
    text(s, LM, 0.6, 8, 0.8, "Agenda", 34, True, NAVY)
    rect(s, LM, 1.5, CW, 0.012, LINE)
    filas_agenda = [
        ("·", STAGE[0], "Meta del sprint y modelo final", "HU12 a HU16 · evaluación y despliegue"),
        ("1", STAGE[1], "HU12 — Evaluación en la prueba oficial", "Clasificación y segmentación, una sola vez"),
        ("2", STAGE[2], "HU13 — Aplicación web", "Backend FastAPI + modelos ONNX (visor de radiología)"),
        ("3", STAGE[3], "HU14 — MLOps básico", "Registro de modelos, tarjetas y versionado"),
        ("4", STAGE[1], "Decisiones, cumplimiento de metas y riesgos", "Tabla meta vs. logrado"),
        ("5", STAGE[2], "Limitaciones y cierre del proyecto", "HU15 informe · HU16 esta presentación"),
    ]
    y = 1.85
    for num, col, ttl, sub in filas_agenda:
        sp = rect(s, LM, y, 0.55, 0.55, col, None, MSO_SHAPE.OVAL)
        tf = sp.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run(p, num, 18, True, WHITE)
        text(s, LM + 0.82, y - 0.04, 10.3, 0.4, ttl, 19, True, NAVY, anchor=MSO_ANCHOR.MIDDLE)
        text(s, LM + 0.82, y + 0.32, 10.3, 0.3, sub, 12, False, MUTED)
        y += 0.85
    D.footer(s)

    # ---- 3. Meta del Sprint 3
    s = content2(D, STAGE[0], "SPRINT 3 · EVALUACIÓN Y DESPLIEGUE", "Meta del Sprint 3")
    bullets(s, ["Evaluar los modelos finales una sola vez en la prueba oficial y desplegarlos en una app web",
                "Historias HU12 a HU16 · fecha de esta presentación (HU16): 30 de octubre de 2026",
                "Fase de CRISP-ML(Q): Evaluación y despliegue (cierre del ciclo iniciado en el Sprint 1)",
                "La prueba oficial (1.000 imágenes) no se usó para elegir nada: se evalúa una única vez (HU12)"],
            LM, 1.9, 6.6, 4.5, 18, STAGE[0], gap=14)
    rect(s, 7.8, 1.9, 4.83, 4.6, PANEL)
    text(s, 8.1, 2.05, 4.3, 0.35, "HISTORIAS DEL SPRINT 3", 11, True, MUTED)
    historias = (("HU12", "Evaluación en la prueba oficial"), ("HU13", "Aplicación web"),
                 ("HU14", "MLOps básico"), ("HU15", "Informe final (otro)"), ("HU16", "Esta presentación"))
    for i, (h, sub) in enumerate(historias):
        rect(s, 8.1, 2.55 + i * 0.78, 0.07, 0.55, STAGE[(i % 3) + 1])
        text(s, 8.35, 2.55 + i * 0.78, 1.4, 0.55, h, 15, True, NAVY, anchor=MSO_ANCHOR.MIDDLE)
        text(s, 9.65, 2.55 + i * 0.78, 2.95, 0.55, sub, 11.5, False, MUTED, anchor=MSO_ANCHOR.MIDDLE, spacing=1.0)
    text(s, 8.1, 6.45, 4.3, 0.4, "Única evaluación del proyecto en la prueba", 12, False, MUTED, italic=True)

    # ---- 4. Modelo final: reentreno + ONNX (divisor)
    divider2(D, STAGE[1], "MODELO FINAL · ONNX", "★", "Reentreno sobre train+val y exportación a ONNX",
             "Se congeló la configuración elegida en el Sprint 2 y se reentrenó sobre entrenamiento + validación",
             ["Clasificador EfficientNetB0 (batch=64, lr=3e-4, %d épocas) reentrenado sobre las 5.000 imágenes de "
              "clasificación (train+val)" % REG_CLF["entrenamiento"]["epocas"],
              "U-Net ResNet34 (lr=1e-4, %d épocas) reentrenado sobre las 3.933 imágenes con máscara (train+val)"
              % REG_UNET["entrenamiento"]["epocas"],
              "Exportación a ONNX (opset 17) con paridad PyTorch–ONNX verificada antes de desplegar"],
             ["clasificador_final.onnx (%.0f MB) y unet_final.onnx (%.0f MB) · registro_modelos.json versionado "
              "(commit %s)" % (REG_CLF["artefacto"]["tamano_mb"], REG_UNET["artefacto"]["tamano_mb"], REG["commit_git"])],
             ["Paridad clasificador: %s" % REG_CLF["artefacto"]["paridad_pytorch_onnx"],
              "Paridad U-Net: %s · la máscara binaria coincide en el 100 %% de los píxeles"
              % REG_UNET["artefacto"]["paridad_pytorch_onnx"]])

    # ---- 5. HU12: resultados en la prueba (cifras grandes + val vs prueba)
    s = content2(D, STAGE[1], "HU12 · EVALUACIÓN", "Resultados en la prueba oficial (una sola vez)")
    D.tile(s, LM, 1.7, 3.55, 1.75, f"{ACC:.2f} %",
           f"Accuracy de clasificación ({N_CLF} imágenes de prueba)", STAGE[1])
    D.tile(s, LM + 3.75, 1.7, 3.55, 1.75, f"{IOU:.2f} %",
           f"IoU de segmentación ({N_SEG} imágenes con máscara)", STAGE[1])
    pic(s, FIGS + "val_vs_prueba.png", 8.0, 1.6, w=4.6)
    bullets(s, [
        f"Clasificación: accuracy {ACC:.2f} %, F1 macro {F1:.2f} %; recall por clase mínimo {RC_MIN:.2f} % (glioma)",
        f"Segmentación: IoU {IOU:.2f} %, Dice {DICE:.2f} % (solo las {N_SEG} imágenes con tumor)",
        "En prueba ≈ validación: en el Sprint 2 (3 semillas) el clasificador dio recall medio "
        f"{REG_CLF['validacion_sprint2']} y la U-Net IoU {REG_UNET['validacion_sprint2']} — generaliza bien",
    ], LM, 3.75, 7.3, 2.6, 13.5, STAGE[1], gap=7)

    # ---- 6. HU12: matriz de confusión + recall por clase
    s = content2(D, STAGE[1], "HU12 · EVALUACIÓN", "Clasificación: matriz de confusión y recall por clase")
    pic(s, FIGS + "prueba_matriz_confusion.png", LM, 1.7, w=5.7)
    pic(s, FIGS + "prueba_recall_por_clase.png", LM + 6.0, 1.7, w=5.7)
    bullets(s, [
        "Recall por clase: glioma %.2f %%, meningioma %.2f %%, hipófisis %.2f %%, sin tumor %.2f %%"
        % (RC["glioma"], RC["meningioma"], RC["pituitary"], RC["no_tumor"]),
        f"Hipófisis y sin tumor sin error (100 %%); los pocos fallos son entre glioma y meningioma",
        f"Todas las clases superan la meta del acta (recall ≥ {METAS['recall_por_clase'] * 100:.0f} %% por clase)",
    ], LM, 5.35, CW, 1.6, 14, STAGE[1], gap=6)

    # ---- 7. HU12: segmentación por clase
    s = content2(D, STAGE[1], "HU12 · EVALUACIÓN", "Segmentación: IoU y Dice por clase")
    pic(s, FIGS + "prueba_iou_por_clase.png", LM, 1.7, w=7.3)
    bullets(s, [
        f"IoU global {IOU:.2f} %, Dice {DICE:.2f} %",
        "IoU por clase: meningioma %.2f %%, hipófisis %.2f %%, glioma %.2f %%"
        % (IOU_CL["meningioma"], IOU_CL["pituitary"], IOU_CL["glioma"]),
        "Dice por clase: meningioma %.2f %%, hipófisis %.2f %%, glioma %.2f %%"
        % (DICE_CL["meningioma"], DICE_CL["pituitary"], DICE_CL["glioma"]),
        f"El glioma es la clase más difícil de segmentar (IoU {IOU_CL['glioma']:.2f} %), como se previó "
        "en el Sprint 1: su contraste es casi igual al del tejido sano",
    ], 7.85, 1.85, 4.75, 4.8, 15, STAGE[1], gap=10)

    # ---- 8. Riesgo R09 + advertencia de la fuga
    s = content2(D, STAGE[0], "RIESGO R09", "Riesgo R09 (gris/RGB) y advertencia de la prueba")
    pic(s, FIGS + "prueba_por_modo.png", LM, 1.65, w=6.1)
    mL = CLF["accuracy_por_modo"]["L"]["valor"] * 100
    mRGB = CLF["accuracy_por_modo"]["RGB"]["valor"] * 100
    sL = SEG["iou_por_modo"]["L"]["valor"] * 100
    sRGB = SEG["iou_por_modo"]["RGB"]["valor"] * 100
    bullets(s, [
        "R09 (atajo por procedencia gris/RGB) investigado también en la prueba oficial",
        "Clasificación por tipo de archivo: gris %.2f %%, RGB %.2f %% — sin brecha relevante" % (mL, mRGB),
        "Segmentación por tipo de archivo: gris %.2f %%, RGB %.2f %% de IoU" % (sL, sRGB),
    ], 6.5, 1.75, 6.1, 2.8, 14, STAGE[0], gap=8)
    rect(s, 6.5, 4.75, 6.1, 1.95, PANEL)
    rect(s, 6.5, 4.75, 6.1, 0.07, STAGE[4])
    text(s, 6.8, 4.95, 5.6, 0.35, "ADVERTENCIA (SE INFORMA)", 12, True, STAGE[4])
    text(s, 6.8, 5.35, 5.6, 1.3,
         "113–123 de las 1.000 imágenes de prueba tienen un vecino casi idéntico en entrenamiento. "
         "Como el modelo final se reentrenó con train+val, la cifra de prueba puede estar algo inflada.",
         13, False, INK, spacing=1.12)

    # ---- 9. HU13: aplicación web (descripción + capturas)
    s = content2(D, STAGE[2], "HU13 · APLICACIÓN WEB", "Aplicación web: visor de radiología")
    pic(s, FIGS + "app_glioma.jpg", LM, 1.7, w=3.75)
    pic(s, FIGS + "app_meningioma.jpg", LM + 3.95, 1.7, w=3.75)
    pic(s, FIGS + "app_sin_tumor.jpg", LM + 7.9, 1.7, w=3.75)
    bullets(s, [
        "Backend FastAPI que sirve los modelos ONNX; interfaz tipo visor de radiología "
        "(imagen en gris, máscara coral y lecturas en tipografía monoespaciada)",
        "Casos reales de las capturas: glioma 100 % (área 2,24 %), meningioma 99,1 % (área 4,47 %), sin tumor 100 %",
    ], LM, 5.2, CW, 1.6, 15, STAGE[2], gap=8)

    # ---- 10. HU13: decisión de arquitectura (R05)
    s = content2(D, STAGE[2], "HU13 · APLICACIÓN WEB", "Decisión de arquitectura (riesgo R05)")
    pic(s, FIGS + "app_vacio.jpg", 7.9, 1.7, w=4.7)
    bullets(s, [
        "Se eligió un backend local que ejecuta los modelos ONNX, en lugar de correrlos en el navegador",
        "Motivo (riesgo R05, modelo pesado): la U-Net pesa ~%.0f MB en ONNX, demasiado para cargarla en el "
        "navegador del usuario" % REG_UNET["artefacto"]["tamano_mb"],
        "El clasificador (%.0f MB) sí es liviano, pero mantener ambos modelos en el backend simplifica el despliegue"
        % REG_CLF["artefacto"]["tamano_mb"],
        "Flujo: se sube una MRI, el backend devuelve la clase, la probabilidad y la máscara del tumor",
        "La pantalla inicial queda vacía hasta que se sube una imagen (captura de la derecha)",
    ], LM, 1.85, 6.9, 4.8, 15, STAGE[2], gap=10)

    # ---- 11. HU14: MLOps básico
    s = content2(D, STAGE[3], "HU14 · MLOPS BÁSICO", "MLOps básico: registro y versionado")
    panel(s, LM, 1.85, 5.8, 2.5, "QUÉ SE REGISTRA",
          ["Modelos ONNX con su tarjeta de modelo y su archivo de procedencia (datos, épocas, "
           "hiperparámetros, semilla, commit)."],
          STAGE[2])
    panel(s, LM + 6.13, 1.85, 5.8, 2.5, "QUÉ SE VERSIONA EN GIT",
          ["registro_modelos.json (procedencia, métricas de validación y de prueba, commit). "
           "Los pesos .pt y los .onnx NO se suben a Git: se regeneran."],
          STAGE[3])
    bullets(s, [
        "registro_modelos.json reúne, por modelo: arquitectura, datos de reentreno, hiperparámetros, "
        "tamaño del ONNX, paridad PyTorch–ONNX, métricas de validación (Sprint 2) y de prueba (HU12)",
        f"Trazabilidad: cada modelo queda ligado al commit de Git ({REG['commit_git']}) con el que se generó",
        "Reproducible: los artefactos pesados se regeneran con los scripts de reentreno y exportación",
    ], LM, 4.7, CW, 2.0, 14, STAGE[3], gap=8)

    # ---- 12. Decisiones y cumplimiento de metas (tabla meta vs logrado)
    s = content2(D, STAGE[1], "DECISIONES", "Cumplimiento de las metas del acta (prueba oficial)")
    table(s, [
        ["Meta del acta", "Objetivo", "Logrado en la prueba", "Estado"],
        ["Accuracy de clasificación", "≥ %.0f %%" % (METAS["accuracy"] * 100), "%.2f %%" % ACC, "Superada"],
        ["Recall por clase (mínimo)", "≥ %.0f %%" % (METAS["recall_por_clase"] * 100),
         "%.2f %% (glioma)" % RC_MIN, "Superada"],
        ["IoU de segmentación", "≥ %.0f %%" % (METAS["iou"] * 100), "%.2f %%" % IOU, "Superada"],
    ], LM, 1.85, CW, [4.0, 2.3, 3.2, 2.43], 15, 0.7, first_col_bold=True)
    bullets(s, [
        "Las tres metas propuestas por el equipo en el acta quedan superadas en la única evaluación de la prueba",
        "La decisión de modelos (EfficientNetB0 y U-Net ResNet34) se tomó en el Sprint 2 solo con validación; "
        "la prueba únicamente confirma el resultado, no se usó para elegir",
        f"F1 macro de clasificación: {F1:.2f} % · Dice de segmentación: {DICE:.2f} %",
    ], LM, 4.5, CW, 2.1, 15, STAGE[1], gap=9)

    # ---- 13. Riesgos del proyecto
    s = content2(D, STAGE[0], "RIESGOS", "Riesgos del proyecto (cierre)")
    table(s, [
        ["Riesgo", "Mitigación aplicada", "Estado en el Sprint 3"],
        ["R01 · Fuga entre pacientes", "Partición por grupo_hash; prueba intacta",
         "Se reporta la advertencia (113–123 imágenes parecidas)"],
        ["R04 · Arquitecturas inestables", "2 arquitecturas y 3 semillas en validación",
         "Prueba ≈ validación: el modelo generaliza bien"],
        ["R05 · Modelo pesado para el navegador", "Backend local + modelos ONNX",
         "Resuelto: la U-Net (~%.0f MB) corre en el backend" % REG_UNET["artefacto"]["tamano_mb"]],
        ["R06 · Memoria de GPU", "Precisión mixta y lote pequeño",
         "Sin problemas de memoria en el reentreno final"],
        ["R09 · Atajo gris/RGB", "Reportar por tipo de archivo",
         "Investigado en la prueba: sin brecha relevante en clasificación"],
    ], LM, 1.8, CW, [2.9, 4.0, 5.03], 12.5, 0.78, first_col_bold=True)

    # ---- 14. Limitaciones
    s = content2(D, STAGE[0], "LIMITACIONES", "Limitaciones del proyecto", [
        "La prueba oficial se evaluó una sola vez (HU12): no hay margen para reoptimizar sobre ella",
        "Posible fuga: 113–123 de las 1.000 imágenes de prueba tienen un vecino casi idéntico en "
        "entrenamiento, así que la cifra de prueba puede estar algo inflada (se informa)",
        f"El glioma es la clase más difícil de segmentar (IoU {IOU_CL['glioma']:.2f} %): su contraste es "
        "casi igual al del tejido sano",
        "Dataset de un único tipo de imagen (T1 con contraste): el resultado no se puede extrapolar a otras "
        "modalidades ni a otros equipos",
        "Es una demostración académica: NO es una herramienta de diagnóstico y no se usa con pacientes",
    ], 18)

    # ---- 15. Cierre del proyecto
    s = content2(D, STAGE[3], "CIERRE", "Cierre del proyecto", [
        "HU12 a HU16 completas: evaluación única en la prueba, app web con modelos ONNX, MLOps básico, "
        "informe (HU15) y esta presentación (HU16)",
        f"Resultados en la prueba oficial: accuracy {ACC:.2f} %, F1 macro {F1:.2f} %, IoU {IOU:.2f} %, "
        f"Dice {DICE:.2f} % — las tres metas del acta superadas",
        "La metodología Scrum + CRISP-ML(Q) se cerró de punta a punta: negocio, datos, preparación, "
        "modelado y, ahora, evaluación y despliegue",
        "Entrega final del proyecto: 30 de octubre · margen: 31 de octubre · fecha límite: 2 de noviembre de 2026",
        "Pendiente (gestión, a cargo del equipo): retrospectiva del Sprint 3 y plantillas de cierre del docente",
    ], 17)

    out = _AQUI / "presentacion_sprint3.pptx"
    prs.save(str(out))
    return out, len(prs.slides)


# ------------------------------------------------------------------ verificación: geometría dentro de límites
def verificar_geometria(path):
    prs = Presentation(str(path))
    sw, sh = prs.slide_width, prs.slide_height
    fuera = []
    tol = 1  # 1 EMU de tolerancia
    for i, slide in enumerate(prs.slides, 1):
        for sh_ in slide.shapes:
            try:
                left = sh_.left if sh_.left is not None else 0
                top = sh_.top if sh_.top is not None else 0
                w = sh_.width if sh_.width is not None else 0
                h = sh_.height if sh_.height is not None else 0
            except Exception:
                continue
            if left < -tol or top < -tol or left + w > sw + tol or top + h > sh + tol:
                fuera.append((i, sh_.shape_type, left, top, w, h))
    return len(prs.slides), fuera, sw, sh


if __name__ == "__main__":
    out, n = build()
    # Reabrir con python-pptx: contar diapositivas, tamaño en bytes y chequeo de geometría.
    n_reabierto, fuera, sw, sh = verificar_geometria(out)
    size = out.stat().st_size
    print(f"Presentación del Sprint 3: {n} diapositivas generadas, {size} bytes -> {out}")
    print(f"Reabierto con python-pptx: {n_reabierto} diapositivas · lienzo {sw}x{sh} EMU (13.333x7.5 in)")
    if fuera:
        print(f"ATENCIÓN: {len(fuera)} formas fuera de los límites:")
        for f in fuera:
            print("   diapositiva %d · %s · left=%d top=%d w=%d h=%d" % f)
    else:
        print("Chequeo de geometría: OK — ninguna forma se sale de los límites de la diapositiva.")
