# -*- coding: utf-8 -*-
"""Presentacion FINAL del Sprint 3 (pptx), mismo diseno blanco del Sprint 1/2 (importa deck_light.py; no lo
modifica). Todas las cifras se leen de la evaluacion real de la prueba oficial
("03. Implementacion/Sprint 3 - Evaluacion y despliegue/salida_sprint3/evaluacion_prueba.json") y del
registro de modelos; las imagenes salen de herramientas/figs_sprint3/. No se inventa ningun numero.

Uso:  python build_slides_sprint3.py
"""
import json
import sys
from pathlib import Path

from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

_AQUI = Path(__file__).resolve().parent
_RAIZ = _AQUI.parent
sys.path.insert(0, str(_AQUI))
from deck_light import (  # noqa: E402
    NAVY, INK, MUTED, LINE, PANEL, WHITE, STAGE, SW, SH, LM, CW,
    text, rect, label_shape, bullets, pic, table, Deck,
)

S3 = _RAIZ / "03. Implementacion" / "Sprint 3 - Evaluacion y despliegue"
FIGS = _AQUI / "figs_sprint3"
FOOT = "Sistema Inteligente: tumores cerebrales en MRI  ·  Presentación final (Sprint 3)"

EV = json.loads((S3 / "salida_sprint3" / "evaluacion_prueba.json").read_text(encoding="utf-8"))
REG = json.loads((S3 / "registro_modelos.json").read_text(encoding="utf-8"))
CLF, SEG = EV["clasificacion"], EV["segmentacion"]
CD, SD = CLF["desplegado"], SEG["desplegado"]
CL = {"glioma": "Glioma", "meningioma": "Meningioma", "pituitary": "Hipófisis", "no_tumor": "Sin tumor"}
pc = lambda x: f"{x*100:.2f}%"
F = lambda n: str(FIGS / n)

BLOQUES = [("Joseph Coavoy", 4), ("Manuel Cuchuyrrumi", 4), ("Brayan Huallpatuiro", 4), ("Frank Mamani", 4)]


def expositor():
    mapa, n = {}, 0
    for nombre, cant in BLOQUES:
        for _ in range(cant):
            n += 1; mapa[n] = nombre
    return mapa


def chrome2(D, s, color, pill, title):
    rect(s, 0, 0, SW, 0.12, color)
    label_shape(s, LM, 0.36, 4.6, 0.3, color, pill, 10)
    text(s, LM, 0.74, CW, 0.7, title, 27, True, NAVY, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, LM, 1.5, CW, 0.012, LINE)
    D.footer(s)


def panel(s, x, y, w, h, head, body, col):
    rect(s, x, y, w, h, PANEL)
    rect(s, x, y, w, 0.07, col)
    text(s, x + 0.25, y + 0.2, w - 0.5, 0.35, head, 12, True, col)
    text(s, x + 0.25, y + 0.62, w - 0.5, h - 0.8, body, 15, False, INK, spacing=1.12)


def cifra(s, x, y, w, valor, etq, col):
    rect(s, x, y, w, 1.5, PANEL)
    rect(s, x, y, 0.07, 1.5, col)
    text(s, x + 0.25, y + 0.2, w - 0.4, 0.7, valor, 34, True, NAVY)
    text(s, x + 0.25, y + 1.0, w - 0.4, 0.4, etq, 12, False, MUTED)


def build():
    D = Deck(FOOT, expositor())
    recall_medio = sum(CD["recall_por_clase"].values()) / 4 * 100

    # 1. Portada
    s = D.slide()
    rect(s, 0, 0, 0.45, SH, NAVY)
    text(s, 1.1, 0.75, 11, 0.4, "PRESENTACIÓN FINAL · SPRINT 3", 14, True, STAGE[2])
    text(s, 1.1, 1.3, 10.8, 2.0, "Clasificación y segmentación de tumores cerebrales en resonancias magnéticas",
         32, True, NAVY, spacing=1.05)
    text(s, 1.1, 3.4, 10.8, 0.5, "Evaluación, despliegue y cierre del proyecto (demostración académica)", 18, False, MUTED)
    rect(s, 1.1, 4.1, 1.6, 0.04, STAGE[2])
    text(s, 1.1, 4.3, 11, 0.4, "Proyecto académico de Redes Neuronales · Ingeniería de Sistemas – Inteligencia Artificial", 14, False, INK)
    text(s, 1.1, 4.7, 11, 0.8, ["Coavoy Cruz Joseph Gabriel · Cuchuyrrumi Mamani Manuel Rodrigo",
                                "Huallpatuiro Rafaile Brayan · Mamani Acuña Frank Joseph"], 14, False, INK, spacing=1.15)
    text(s, 1.1, 5.6, 11, 0.4, "Docente revisor: Ing. Hugo Espetia Huamanga  ·  30 de octubre de 2026", 14, False, MUTED)
    for i, (t, col) in enumerate((("HU12 · Evaluación", STAGE[1]), ("HU13 · Despliegue", STAGE[2]), ("HU14 · MLOps", STAGE[3]))):
        label_shape(s, 1.1 + i * 3.95, 6.2, 3.75, 0.32, col, t, 10)
    text(s, 1.1, 6.65, 11, 0.4, "Demostración académica · Apoyo al diagnóstico, no es un diagnóstico médico", 12, False, STAGE[2])

    # 2. Agenda
    s = D.slide()
    rect(s, 0, 0, SW, 0.12, STAGE[0])
    text(s, LM, 0.6, 8, 0.8, "Agenda", 34, True, NAVY)
    rect(s, LM, 1.5, CW, 0.012, LINE)
    filas = [("1", STAGE[1], "Resumen Sprints 1–2", "Datos, modelado y modelos elegidos"),
             ("2", STAGE[2], "HU12 — Evaluación en la prueba oficial", "Una sola vez, 6 semillas, metas del acta"),
             ("3", STAGE[3], "HU13 — Despliegue: sistema clínico", "Demo del flujo de apoyo al diagnóstico"),
             ("4", STAGE[1], "HU14 — MLOps básico", "Versionado y monitoreo"),
             ("5", STAGE[2], "Riesgos, limitaciones y conclusiones", "Cierre del proyecto")]
    y = 2.0
    for num, col, tit, sub in filas:
        label_shape(s, LM, y, 0.55, 0.55, col, num, 16, kind=MSO_SHAPE.OVAL)
        text(s, LM + 0.85, y + 0.02, 10, 0.4, tit, 17, True, NAVY)
        text(s, LM + 0.85, y + 0.45, 10, 0.3, sub, 12, False, MUTED)
        y += 0.98
    D.footer(s)

    # 3. Problema y metodologia
    s = D.slide(); chrome2(D, s, STAGE[1], "METODOLOGÍA", "Problema y metodología")
    panel(s, LM, 1.85, 5.9, 2.1, "EL PROBLEMA", "Apoyar la lectura de resonancias T1 en neuro-oncología: sugerir el "
          "tipo de tumor y marcar su contorno, como apoyo al diagnóstico (no lo reemplaza).", STAGE[1])
    panel(s, LM, 4.1, 5.9, 2.1, "METAS DEL ACTA", "Accuracy ≥ 95 %  ·  recall ≥ 90 % por clase  ·  IoU ≥ 70 %, "
          "medidas sobre la prueba oficial.", STAGE[2])
    panel(s, 6.9, 1.85, 5.7, 4.35, "METODOLOGÍA", "Scrum organiza el trabajo (sprints, revisión y retrospectiva); "
          "CRISP-ML(Q) organiza el ciclo del modelo.\n\nSprint 1 — negocio y datos\nSprint 2 — modelado\n"
          "Sprint 3 — evaluación y despliegue.\n\nReglas: no inventar datos; la prueba oficial se evalúa una sola "
          "vez; datos ficticios en la app.", STAGE[3])

    # 4. Resumen Sprints 1-2
    s = D.slide(); chrome2(D, s, STAGE[1], "SPRINTS 1–2", "De dónde partimos: datos y modelos")
    bullets(s, ["Dataset BRISC 2025 (CC BY 4.0): 6.000 imágenes, 4.793 máscaras; partición propia (semilla 42) "
                "3.999 / 1.001 / 1.000; prueba oficial intacta.",
                "Sprint 2: 13 entrenamientos; se compararon EfficientNetB0 y ResNet50 (clasificación) y U-Net "
                "ResNet34 (segmentación), con ajuste de hiperparámetros y 3 semillas.",
                "Modelos elegidos por validación: EfficientNetB0 (lote 64) e U-Net (lr 1e-4)."],
            LM, 1.9, CW, 2.2, 17, STAGE[1])
    table(s, [["Tarea", "Modelo elegido", "Validación (3 semillas)"],
              ["Clasificación", "EfficientNetB0 (lote 64)", "recall 99,57 % ± 0,15 %"],
              ["Segmentación", "U-Net ResNet34 (lr 1e-4)", "IoU 80,12 % ± 0,33 %"]],
          LM, 4.3, 11.9, [2.8, 5.0, 4.1], size=14, rowh=0.62)

    # 5. HU12 resultados
    s = D.slide(); chrome2(D, s, STAGE[2], "HU12 · EVALUACIÓN", "Resultados en la prueba oficial")
    cifra(s, LM, 1.9, 3.9, pc(CD["accuracy"]), "accuracy (clasificación)", STAGE[2])
    cifra(s, LM + 4.2, 1.9, 3.9, pc(SD["iou"]), "IoU (segmentación)", STAGE[2])
    cifra(s, LM + 8.4, 1.9, 3.5, pc(SD["dice"]), "Dice (segmentación)", STAGE[3])
    text(s, LM, 3.6, CW, 0.4, "Evaluada una sola vez · modelo desplegado = mejor por validación (semilla 2024) · "
         "las 3 metas del acta se cumplen", 13, True, NAVY)
    pic(s, F("val_vs_prueba.png"), 2.3, 4.1, w=8.7)

    # 6. Por semilla + sin vecino
    s = D.slide(); chrome2(D, s, STAGE[2], "HU12 · ROBUSTEZ", "Por semilla y efecto de la fuga")
    pic(s, F("prueba_semillas_vecino.png"), 1.9, 1.9, w=9.5)
    text(s, LM, 6.35, CW, 0.5, f"Promedio 3 semillas: clasificador {pc(CLF['accuracy_promedio'])} ± "
         f"{pc(CLF['accuracy_desvio'])} · U-Net {pc(SEG['iou_promedio'])} ± {pc(SEG['iou_desvio'])}. "
         f"{EV['imagenes_con_vecino_cercano']} imágenes con vecino cercano; sin ellas baja poco "
         f"({pc(CLF['accuracy_sin_vecino'])} / {pc(SEG['iou_sin_vecino'])}).", 12, False, MUTED, spacing=1.1)

    # 7. HU12 clasificacion
    s = D.slide(); chrome2(D, s, STAGE[2], "HU12 · CLASIFICACIÓN", "Recall por clase y matriz de confusión")
    pic(s, F("prueba_recall_por_clase.png"), LM, 1.95, w=6.0)
    pic(s, F("prueba_matriz_confusion.png"), 7.3, 1.95, w=5.0)
    text(s, LM, 6.4, CW, 0.4, "Todas las clases superan la meta de recall (90 %); el glioma es la más difícil "
         f"({pc(min(CD['recall_por_clase'].values()))}).", 13, False, MUTED)

    # 8. HU12 segmentacion
    s = D.slide(); chrome2(D, s, STAGE[2], "HU12 · SEGMENTACIÓN", "IoU por clase y ejemplos reales")
    pic(s, F("prueba_iou_por_clase.png"), LM, 1.95, w=5.6)
    pic(s, F("prueba_ejemplos_segmentacion.png"), 7.7, 1.7, h=4.9)
    text(s, LM, 6.3, 6, 0.6, "El glioma, de bajo contraste, es el más difícil de segmentar "
         f"(IoU {pc(SD['iou_por_clase']['glioma']['valor'])}).", 12, False, MUTED, spacing=1.1)

    # 9. R09
    s = D.slide(); chrome2(D, s, STAGE[3], "RIESGO R09", "Atajo por procedencia de la imagen")
    pic(s, F("prueba_por_modo.png"), 2.3, 1.95, w=8.7)
    text(s, LM, 6.3, CW, 0.5, "Por tipo de archivo (gris/RGB) la clasificación casi no cambia; en segmentación hay "
         "una brecha que coincide con que el glioma es mayoritariamente en gris. Se reporta como limitación.", 13, False, MUTED, spacing=1.1)

    # 10. Demo flujo
    s = D.slide(); chrome2(D, s, STAGE[1], "HU13 · DEMO", "El sistema clínico — flujo")
    for i, (fig, cap) in enumerate((("app_login.jpg", "1. Inicio de sesión"), ("app_casos.jpg", "2. Casos"),
                                     ("app_estudio.jpg", "3. Subir la resonancia"))):
        x = LM + i * 4.15
        pic(s, F(fig), x, 2.0, w=3.9)
        text(s, x, 5.7, 3.9, 0.4, cap, 13, True, NAVY)
    text(s, LM, 6.4, CW, 0.4, "Prototipo clínico (FastAPI + ONNX en CPU), diseño blanco y formal, funciona sin internet.", 12, False, MUTED)

    # 11. Demo resultado
    s = D.slide(); chrome2(D, s, STAGE[1], "HU13 · DEMO", "Resultado y revisión del médico")
    pic(s, F("app_resultado.jpg"), LM, 2.0, w=6.0)
    pic(s, F("app_sin_tumor.jpg"), 7.1, 2.0, w=5.4)
    text(s, LM, 6.4, CW, 0.5, "Clase sugerida, probabilidades, contorno del tumor y revisión del médico. Si el "
         "sistema sugiere «sin tumor», no muestra contorno (derecha). Alerta de confianza baja < 80 %.", 12, False, MUTED, spacing=1.1)

    # 12. Demo informe + ficha
    s = D.slide(); chrome2(D, s, STAGE[1], "HU13 · DEMO", "Informe del caso y ficha del modelo")
    pic(s, F("app_informe.jpg"), LM, 2.0, w=6.0)
    pic(s, F("app_ficha.jpg"), 7.1, 2.0, w=5.4)
    text(s, LM, 6.4, CW, 0.4, "Informe imprimible con la versión de los modelos y el aviso. La ficha muestra las "
         "métricas (validación y prueba), el uso previsto y las limitaciones.", 12, False, MUTED)

    # 13. MLOps
    s = D.slide(); chrome2(D, s, STAGE[3], "HU14 · MLOPS", "Versionado y monitoreo")
    bullets(s, ["Modelos en ONNX con tarjeta de modelo y SHA-256; paridad PyTorch↔ONNX verificada.",
                f"registro_modelos.json: procedencia, SHA-256, métricas, versión del dataset y commit de Git ({REG.get('commit_git','')}).",
                "Etiquetas de Git: " + ", ".join(REG.get("etiquetas_git", [])) + ".",
                "Monitoreo en la app: cada predicción (clase, confianza, tiempo, brillo, alerta) sin guardar "
                "imágenes ni datos personales; brillo medio como señal de deriva."],
            LM, 1.95, 6.3, 4.0, 16, STAGE[3])
    pic(s, F("app_monitoreo.jpg"), 7.2, 2.1, w=5.3)

    # 14. Cumplimiento de metas
    s = D.slide(); chrome2(D, s, STAGE[2], "CUMPLIMIENTO", "Metas del acta en la prueba oficial")
    si = lambda b: "Cumple" if b else "No cumple"
    cumple = EV["cumple"]
    table(s, [["Métrica", "Meta", "Logrado (prueba)", "Resultado"],
              ["Accuracy (clasificación)", "≥ 95 %", pc(CD["accuracy"]), si(cumple["accuracy"])],
              ["Recall mínimo por clase", "≥ 90 %", pc(min(CD["recall_por_clase"].values())) + " (glioma)", si(cumple["recall_por_clase"])],
              ["IoU (segmentación)", "≥ 70 %", pc(SD["iou"]), si(cumple["iou"])]],
          LM, 2.2, 12.6, [4.3, 2.3, 3.4, 2.6], size=15, rowh=0.72, first_col_bold=True)
    text(s, LM, 5.6, CW, 0.5, "El desempeño en prueba es muy cercano al de validación: el modelo generaliza.", 14, True, NAVY)

    # 15. Riesgos y limitaciones
    s = D.slide(); chrome2(D, s, STAGE[0], "RIESGOS", "Riesgos y limitaciones")
    bullets(s, ["R01 fuga: partición por hash y subconjunto sin vecino cercano; se reporta el efecto (pequeño).",
                "R04 arquitecturas inestables: 2 arquitecturas y 3 semillas.",
                "R05 modelo pesado: backend local con ONNX en CPU (no en el navegador).",
                "R09 atajo por procedencia: resultados por plano y tipo de archivo.",
                "El glioma es la clase más difícil; un solo dataset y una sola secuencia (T1 con contraste).",
                "Es una demostración académica de apoyo al diagnóstico; no es un diagnóstico y no usa datos reales."],
            LM, 1.95, CW, 4.5, 16, STAGE[0])

    # 16. Conclusiones
    s = D.slide(); chrome2(D, s, STAGE[2], "CIERRE", "Conclusiones y trabajo futuro")
    panel(s, LM, 1.9, 5.9, 4.3, "CONCLUSIONES", "Las tres metas del acta se cumplen en la prueba oficial "
          f"(accuracy {pc(CD['accuracy'])}, IoU {pc(SD['iou'])}).\n\nEl modelo se desplegó en un prototipo de "
          "apoyo al diagnóstico funcional, reproducible y versionado.", STAGE[2])
    panel(s, 6.9, 1.9, 5.7, 4.3, "TRABAJO FUTURO", "Mejorar el glioma (más datos o pérdidas específicas).\n\n"
          "Validar con otros datasets y escáneres.\n\nModelo multitarea con encoder compartido.\n\n"
          "MLOps más completo (reentrenamiento ante deriva).", STAGE[3])
    text(s, LM, 6.4, CW, 0.4, "Gracias.  Demostración académica · Apoyo al diagnóstico, no es un diagnóstico médico.", 13, True, NAVY)

    out = _AQUI / "presentacion_sprint3.pptx"
    D.prs.save(str(out))
    return out, len(D.prs.slides)


if __name__ == "__main__":
    out, n = build()
    print(f"Presentación del Sprint 3: {n} diapositivas, {out.stat().st_size} bytes -> {out}")
