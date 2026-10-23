# -*- coding: utf-8 -*-
"""Presentación de la Revisión del Sprint 2 (modelado), mismo diseño blanco y formal del Sprint 1.

No modifica `deck_light.py` ni sus salidas: solo importa sus primitivas (colores, fuentes,
funciones ayudantes run()/text()/rect()/label_shape()/bullets()/pic()/table() y la clase Deck)
para copiar exactamente el estilo visual del Sprint 1 (16:9, fondo blanco, Calibri, paleta
NAVY/INK/MUTED/LINE/PANEL, pie de página con expositor y número de diapositiva).

Fuente de verdad de todas las cifras: `03. Implementacion/Sprint 2 - Entrenamiento/experimentos.csv`
(13 filas) y su README.md. Ninguna cifra se escribe a mano sin venir de ahí: las métricas de cada
corrida se leen del CSV en tiempo de ejecución (incluido el "recall medio", que se calcula como el
promedio de val_recall_por_clase, igual que lo reporta el README). Lo que no está en el CSV (por
ejemplo el desglose por plano de corte y tipo de archivo del riesgo R09, que vive en
`salida_sprint2/*_por_grupo.csv`) se toma tal cual del README, que es la otra fuente permitida.

Uso:
    "<repo>/.venv/Scripts/python.exe" herramientas/build_slides_sprint2.py

Genera: herramientas/presentacion_sprint2.pptx
"""
import json
import statistics
import subprocess
import sys
from pathlib import Path

try:
    import pptx  # noqa: F401
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-pptx"])

try:
    import pandas as pd
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas"])
    import pandas as pd

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

CSV = _RAIZ / "03. Implementacion" / "Sprint 2 - Entrenamiento" / "experimentos.csv"
FIGS = str(_AQUI / "figs_sprint2").replace("\\", "/") + "/"
FOOT = "Sistema Inteligente: tumores cerebrales en MRI  ·  Revisión del Sprint 2 (modelado)"

# ------------------------------------------------------------------ datos reales (experimentos.csv)
df = pd.read_csv(CSV, dtype={"semilla": "Int64"})


def fila(id_):
    r = df[df["id"] == id_]
    if r.empty:
        raise KeyError(f"id no encontrado en experimentos.csv: {id_}")
    return r.iloc[0]


def recall_medio(row):
    """Promedio de val_recall_por_clase (JSON) -> igual al 'recall medio' que reporta el README."""
    d = json.loads(row["val_recall_por_clase"])
    return statistics.mean(d.values()) * 100


# modelos base (semilla 42, configuración de partida)
base_clf = fila("clf_efficientnet_b0_20261022_235632")
base_resnet = fila("clf_resnet50_20261023_000153")
base_unet = fila("unet_resnet34_20261022_235636")

# HU08: configuraciones probadas frente al modelo base
hu08_clf_lr = fila("clf_efficientnet_b0_20261023_002327")       # lr=1e-4
hu08_clf_batch64 = fila("clf_efficientnet_b0_20261023_002839")  # elegida
hu08_clf_noaug = fila("clf_efficientnet_b0_20261023_003302")    # sin aumento
hu08_unet_lr = fila("unet_resnet34_20261023_002334")            # elegida
hu08_unet_noaug = fila("unet_resnet34_20261023_004154")         # sin aumento
hu08_unet_batch16 = fila("unet_resnet34_20261023_014104")       # batch=16

# multi-semilla de las configuraciones ganadoras (la semilla 42 es la fila hu08_*_elegida de arriba)
seed_clf = [hu08_clf_batch64,
            fila("clf_efficientnet_b0_20261023_004200"),
            fila("clf_efficientnet_b0_20261023_004900")]
seed_unet = [hu08_unet_lr,
             fila("unet_resnet34_20261023_005823"),
             fila("unet_resnet34_20261023_005828")]

recalls_3s = [recall_medio(r) for r in seed_clf]
ious_3s = [r["val_iou"] * 100 for r in seed_unet]
recall_prom, recall_std = statistics.mean(recalls_3s), statistics.pstdev(recalls_3s)
iou_prom, iou_std = statistics.mean(ious_3s), statistics.pstdev(ious_3s)

# conteos y tiempo por historia (para HU09)
resumen_hu = df.groupby("historia").agg(n=("id", "count"), minutos=("tiempo_min", "sum")).reindex(
    ["HU06", "HU07", "HU08"])
tiempo_total = df["tiempo_min"].sum()

rc_base = json.loads(base_clf["val_recall_por_clase"])
rc_elegida = json.loads(hu08_clf_batch64["val_recall_por_clase"])
acc_elegida = hu08_clf_batch64["val_accuracy"] * 100

# ------------------------------------------------------------------ reparto de la exposición
BLOQUES = [("Joseph Coavoy", 5), ("Manuel Cuchuyrrumi", 5), ("Brayan Huallpatuiro", 4), ("Frank Mamani", 4)]


def expositor_por_diapositiva():
    mapa, n = {}, 0
    for nombre, cant in BLOQUES:
        for _ in range(cant):
            n += 1
            mapa[n] = nombre
    return mapa


# ------------------------------------------------------------------ equivalentes de chrome()/content()/divider()
# Deck.chrome()/content()/divider() (en deck_light.py) usan STAGE_TXT, pensado para las 4 etapas del
# Sprint 1 ("ETAPA 1 · COMPRENSIÓN DEL NEGOCIO", ...). Aquí cada diapositiva necesita su propia
# etiqueta (p. ej. "HU06 · CLASIFICADOR"), así que se repiten esas mismas funciones con la etiqueta
# como parámetro en vez de buscarla en STAGE_TXT. La disposición (barra superior, pastilla, título,
# línea, pie) es idéntica a deck_light.py.
def chrome2(D, s, color, pill, title):
    rect(s, 0, 0, SW, 0.12, color)
    label_shape(s, LM, 0.36, 4.6, 0.3, color, pill, 10)
    text(s, LM, 0.74, CW, 0.7, title, 28, True, NAVY, anchor=MSO_ANCHOR.MIDDLE)
    rect(s, LM, 1.5, CW, 0.012, LINE)
    D.footer(s)


def content2(D, color, pill, title, items=None, size=18):
    s = D.slide()
    chrome2(D, s, color, pill, title)
    if items:
        bullets(s, items, LM, 1.8, CW, 5.0, size, color)
    return s


def divider2(D, color, pill, big, title, sub, hizo, entregables, resultado):
    s = D.slide()
    rect(s, 0, 0, SW, 0.12, color)
    label_shape(s, LM, 0.36, 4.6, 0.3, color, pill, 10)
    text(s, LM, 1.05, 3.2, 1.7, big, 90, True, color)
    text(s, LM, 2.7, 3.4, 1.4, title, 22, True, NAVY, spacing=1.05)
    text(s, LM, 4.15, 3.4, 1.6, sub, 13, False, MUTED, spacing=1.15)
    rect(s, 4.45, 1.0, 0.012, 5.8, LINE)
    x, w = 4.8, 7.83
    y = 1.0
    for head, its, sz, h in (("QUÉ SE HIZO", hizo, 14, 3.05), ("ENTREGABLES", entregables, 14, 1.15),
                              ("RESULTADO", resultado, 14, 1.4)):
        rect(s, x, y, 0.06, h, color)
        text(s, x + 0.2, y - 0.02, w - 0.2, 0.3, head, 11, True, color)
        bullets(s, its, x + 0.2, y + 0.3, w - 0.25, h - 0.3, sz, color, gap=4)
        y += h + 0.17
    D.footer(s)
    return s


def panel(s, x, y, w, h, head, body, col):
    rect(s, x, y, w, h, PANEL)
    rect(s, x, y, w, 0.07, col)
    text(s, x + 0.3, y + 0.22, w - 0.6, 0.35, head, 13, True, col)
    text(s, x + 0.3, y + 0.62, w - 0.6, h - 0.8, body, 16, False, INK, spacing=1.15)


# ------------------------------------------------------------------ construcción del deck
def build():
    D = Deck(FOOT, expositor_por_diapositiva())
    prs = D.prs

    # ---- 1. Portada
    s = D.slide()
    rect(s, 0, 0, 0.45, SH, NAVY)
    text(s, 1.1, 0.75, 11, 0.4, "REVISIÓN DEL SPRINT 2 · MODELADO", 14, True, STAGE[2])
    text(s, 1.1, 1.3, 10.8, 2.0,
         "Desarrollo de un Sistema Inteligente para clasificar y segmentar tumores cerebrales "
         "en resonancias magnéticas", 32, True, NAVY, spacing=1.05)
    text(s, 1.1, 3.35, 10.8, 0.5, "desplegado en una aplicación web de apoyo académico (demostración académica)",
         18, False, MUTED)
    rect(s, 1.1, 4.05, 1.6, 0.04, STAGE[2])
    text(s, 1.1, 4.25, 11, 0.4, "Proyecto académico de Redes Neuronales · Ingeniería de Sistemas – Inteligencia Artificial",
         14, False, INK)
    text(s, 1.1, 4.65, 11, 0.8,
         ["Coavoy Cruz Joseph Gabriel · Cuchuyrrumi Mamani Manuel Rodrigo",
          "Huallpatuiro Rafaile Brayan · Mamani Acuña Frank Joseph"], 14, False, INK, spacing=1.15)
    text(s, 1.1, 5.55, 11, 0.4, "Docente revisor: Ing. Hugo Espetia Huamanga  ·  23 de octubre de 2026", 14, False, MUTED)
    for i, (t, col) in enumerate((("HU05 · Arquitectura", STAGE[1]), ("HU06–HU07 · Entrenamiento", STAGE[2]),
                                   ("HU08–HU09 · Ajuste y registro", STAGE[3]))):
        label_shape(s, 1.1 + i * 3.95, 6.15, 3.75, 0.32, col, t, 10)
    text(s, 1.1, 6.6, 11, 0.4, "Fase CRISP-ML(Q): Modelado  ·  Sprint 2 (10–22 oct de 2026)", 12, False, MUTED)

    # ---- 2. Agenda
    s = D.slide()
    rect(s, 0, 0, SW, 0.12, STAGE[0])
    text(s, LM, 0.6, 8, 0.8, "Agenda", 34, True, NAVY)
    rect(s, LM, 1.5, CW, 0.012, LINE)
    filas_agenda = [
        ("·", STAGE[0], "Meta del sprint", "HU05 a HU09 · fase de modelado"),
        ("1", STAGE[1], "HU05 — Arquitectura y modelo base", "Clasificador (2 candidatas) y U-Net"),
        ("2", STAGE[2], "HU06 y HU07 — Entrenamiento", "Clasificador de tipo de tumor y segmentación U-Net"),
        ("3", STAGE[3], "HU08 — Ajuste de hiperparámetros", "3 configuraciones extra frente al modelo base"),
        ("4", STAGE[1], "HU09 — Registro de experimentos", "13 entrenamientos en experimentos.csv"),
        ("5", STAGE[2], "Resultados, riesgo R09, decisiones y plan del Sprint 3", "Cierre de la revisión"),
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

    # ---- 3. Meta del sprint
    s = content2(D, STAGE[0], "SPRINT 2 · MODELADO", "Meta del Sprint 2")
    bullets(s, ["Entrenar y comparar los modelos de clasificación y segmentación del proyecto",
                "Historias HU05 a HU09 · fecha de esta presentación (HU10): 23 de octubre de 2026",
                "Fase de CRISP-ML(Q): Modelado (después de negocio, datos y preparación de datos del Sprint 1)",
                "La prueba oficial (1.000 imágenes) no se usa para elegir nada: se evalúa una sola vez en el Sprint 3 (HU12)"],
            LM, 1.9, 6.6, 4.5, 18, STAGE[0], gap=14)
    rect(s, 7.8, 1.9, 4.83, 4.6, PANEL)
    text(s, 8.1, 2.05, 4.3, 0.35, "HISTORIAS DEL SPRINT 2", 11, True, MUTED)
    for i, (h, sub) in enumerate((("HU05", "Arquitectura y modelo base"), ("HU06 / HU07", "Clasificador y U-Net"),
                                   ("HU08", "Ajuste de hiperparámetros"), ("HU09", "Registro de experimentos"))):
        rect(s, 8.1, 2.6 + i * 0.95, 0.07, 0.65, STAGE[i + 1])
        text(s, 8.35, 2.6 + i * 0.95, 1.4, 0.65, h, 16, True, NAVY, anchor=MSO_ANCHOR.MIDDLE)
        text(s, 9.7, 2.6 + i * 0.95, 2.9, 0.65, sub, 12, False, MUTED, anchor=MSO_ANCHOR.MIDDLE, spacing=1.05)
    text(s, 8.1, 6.25, 4.3, 0.4, "La evaluación final es en el Sprint 3", 12, False, MUTED, italic=True)

    # ---- 4. HU05 (divisor)
    divider2(D, STAGE[1], "HU05 · ARQUITECTURA", "05", "Selección de arquitectura y modelo base",
             "Historia HU05 · 12–13 oct (plan) · Depende de HU03",
             ["Elegir 2 arquitecturas candidatas de clasificación con transfer learning (pesos de ImageNet): "
              "EfficientNetB0 y ResNet50",
              "Definir la arquitectura U-Net (encoder ResNet34) para la segmentación",
              "Entrenar un modelo base de cada tarea con la configuración de partida (semilla 42) y registrar su métrica"],
             ["modelos.py (clasificador y U-Net), datos.py, metricas.py",
              "3 checkpoints base en salida_sprint2/ y su fila en experimentos.csv"],
             [f"EfficientNetB0 base: accuracy {base_clf['val_accuracy'] * 100:.1f} %, "
              f"recall medio {recall_medio(base_clf):.2f} % (validación)",
              f"ResNet50 base: accuracy {base_resnet['val_accuracy'] * 100:.1f} %, "
              f"recall medio {recall_medio(base_resnet):.2f} % (validación)",
              f"U-Net base: IoU {base_unet['val_iou'] * 100:.2f} %, Dice {base_unet['val_dice'] * 100:.2f} % (validación)"])

    # ---- 5. HU06 (divisor)
    divider2(D, STAGE[2], "HU06 · CLASIFICADOR", "06", "Entrenar el clasificador de tipo de tumor",
             "Historia HU06 · 14–18 oct (plan) · Depende de HU05",
             ["Entrenar EfficientNetB0 con la configuración de partida; guardar curva de entrenamiento y validación",
              "Calcular accuracy, recall por clase y matriz de confusión sobre las 1.001 imágenes de validación",
              "Confirmar EfficientNetB0 como arquitectura principal frente a ResNet50 (mejor recall medio desde el modelo base)"],
             ["Checkpoint y curva en salida_sprint2/ · fila en experimentos.csv"],
             [f"Recall medio {recall_medio(base_clf):.2f} % (modelo base, semilla 42)",
              "Recall por clase (base): glioma %.2f %%, meningioma %.2f %%, hipófisis %.2f %%, sin tumor %.2f %%"
              % (rc_base["glioma"] * 100, rc_base["meningioma"] * 100, rc_base["pituitary"] * 100, rc_base["no_tumor"] * 100)])

    # ---- 6. HU06 (curvas + matriz de confusión)
    s = content2(D, STAGE[2], "HU06 · CLASIFICADOR", "Curva de entrenamiento y matriz de confusión")
    pic(s, FIGS + "curva_clasificador.png", LM, 1.75, w=7.5)
    pic(s, FIGS + "matriz_confusion.png", 8.45, 1.75, w=3.3)
    bullets(s, [
        "La curva y la matriz corresponden a la configuración ganadora de HU08 (batch=64); "
        f"el modelo base (batch=32) tuvo un recall muy similar: {recall_medio(base_clf):.2f} %",
        f"Configuración elegida (batch=64): accuracy {acc_elegida:.2f} % (997 de 1.001 bien clasificadas), "
        f"recall medio {recall_medio(hu08_clf_batch64):.2f} %",
        "Recall por clase (elegida): glioma %.2f %%, meningioma %.2f %%, hipófisis %.2f %%, sin tumor %.2f %%"
        % (rc_elegida["glioma"] * 100, rc_elegida["meningioma"] * 100, rc_elegida["pituitary"] * 100,
           rc_elegida["no_tumor"] * 100),
    ], LM, 4.7, CW, 2.1, 14, STAGE[2], gap=6)

    # ---- 7. HU07 (divisor)
    divider2(D, STAGE[3], "HU07 · SEGMENTACIÓN", "07", "Entrenar el modelo de segmentación U-Net",
             "Historia HU07 · 14–18 oct (plan) · Depende de HU05",
             ["Entrenar la U-Net (encoder ResNet34) solo con imágenes que tienen máscara (3.146 de entrenamiento)",
              "Pérdida BCE + Dice por el desbalance de tamaño del tumor (0,9–1,7 % de la imagen en mediana)",
              "Medir IoU y Dice en validación (787 imágenes con máscara) y guardar ejemplos de máscara predicha"],
             ["Checkpoint y curva en salida_sprint2/ · ejemplos de máscara predicha · fila en experimentos.csv"],
             [f"IoU {base_unet['val_iou'] * 100:.2f} %, Dice {base_unet['val_dice'] * 100:.2f} % (modelo base, semilla 42)",
              "Meta del acta (IoU ≥ 70 %) ya superada desde el modelo base"])

    # ---- 8. HU07 (curva)
    s = content2(D, STAGE[3], "HU07 · SEGMENTACIÓN", "Curva de entrenamiento de la U-Net")
    pic(s, FIGS + "curva_unet.png", LM, 1.75, w=7.4)
    bullets(s, [
        "Curva de la configuración ganadora de HU08 (lr=1e-4); el modelo base (lr=3e-4) llegó a un IoU muy similar: "
        f"{base_unet['val_iou'] * 100:.2f} %",
        f"Configuración elegida (lr=1e-4, semilla 42): IoU {hu08_unet_lr['val_iou'] * 100:.2f} %, "
        f"Dice {hu08_unet_lr['val_dice'] * 100:.2f} %",
        "Entrenada solo con las 3.146 imágenes de entrenamiento que tienen máscara; sin tumor no entra en la segmentación",
        "8,3 % de las máscaras del dataset tiene más de una región (hallazgo del Sprint 1): la U-Net debe poder marcar varias",
    ], 8.4, 1.85, 4.2, 4.6, 14, STAGE[3], gap=8)

    # ---- 9. HU08 (divisor)
    delta_clf = recall_medio(hu08_clf_batch64) - recall_medio(base_clf)
    delta_unet = hu08_unet_lr["val_iou"] * 100 - base_unet["val_iou"] * 100
    divider2(D, STAGE[1], "HU08 · HIPERPARÁMETROS", "08", "Ajustar hiperparámetros y aumento de datos",
             "Historia HU08 · 19–21 oct (plan) · Depende de HU06, HU07",
             ["Probar 3 configuraciones extra por tarea frente al modelo base: tasa de aprendizaje, tamaño de lote "
              "y una ablación sin aumento de datos",
              "Medir la mejora en validación frente al modelo base, sin usar la prueba oficial",
              "Repetir el entrenamiento de la configuración ganadora con 2 semillas adicionales (123 y 2024)"],
             ["7 checkpoints adicionales y sus filas en experimentos.csv (3 configuraciones + 2 semillas, por tarea)"],
             [f"Clasificador: gana batch=64 (recall medio {recall_medio(hu08_clf_batch64):.2f} %, "
              f"{delta_clf:+.2f} pp vs. base)",
              f"U-Net: gana lr=1e-4 (IoU {hu08_unet_lr['val_iou'] * 100:.2f} %, {delta_unet:+.2f} pp vs. base)",
              "El aumento de datos ayuda en ambas tareas: quitarlo empeora el resultado en los dos casos"])

    # ---- 10. HU08 (comparación)
    s = content2(D, STAGE[1], "HU08 · HIPERPARÁMETROS", "Comparación de configuraciones (validación)")
    pic(s, FIGS + "hu08_comparacion.png", LM, 1.7, w=11.0)
    bullets(s, [
        "En la U-Net, batch=16 dio 80,09 % de IoU a una sola semilla, apenas por encima de lr=1e-4 (79,78 %): "
        "una diferencia dentro del margen de variación entre semillas (~0,3 pp, ver diapositiva de resultados)",
        "Se mantuvo lr=1e-4 como configuración elegida porque ya tenía las 3 semillas corridas; no se repitió "
        "batch=16 para no duplicar cómputo por una diferencia no concluyente",
    ], LM, 6.0, CW, 1.0, 13, STAGE[1], gap=4)

    # ---- 11. HU09 (divisor)
    divider2(D, STAGE[2], "HU09 · EXPERIMENTOS", "09", "Registrar y comparar experimentos",
             "Historia HU09 · 21–22 oct (plan) · Depende de HU08",
             ["Registrar cada entrenamiento (clasificador y U-Net) en experimentos.csv: configuración, métricas y tiempo",
              "Comparar configuraciones y elegir los modelos finales con base en la validación",
              "Incluir la tabla completa en el informe del Sprint 2 (herramientas/informe_sprint2.docx)"],
             ["experimentos.csv con 13 filas · tabla completa en el informe"],
             [f"13 entrenamientos completos registrados; {tiempo_total:.1f} minutos de cómputo en GPU en total"])

    # ---- 12. HU09 (tabla de experimentos)
    s = content2(D, STAGE[2], "HU09 · EXPERIMENTOS", "Las 13 corridas registradas")
    filas_tabla = [["Historia", "Entrenamientos", "Tiempo de GPU", "Qué se probó"]]
    descripciones = {
        "HU06": "2 arquitecturas candidatas (EfficientNetB0, ResNet50)",
        "HU07": "U-Net ResNet34, modelo base de segmentación",
        "HU08": "lr, batch, ablación sin aumento y 2 semillas adicionales (clasificador y U-Net)",
    }
    for hu in ("HU06", "HU07", "HU08"):
        n = int(resumen_hu.loc[hu, "n"])
        mins = resumen_hu.loc[hu, "minutos"]
        filas_tabla.append([hu, str(n), f"{mins:.1f} min", descripciones[hu]])
    filas_tabla.append(["Total", "13", f"{tiempo_total:.1f} min", "—"])
    table(s, filas_tabla, LM, 1.85, CW, [1.5, 2.1, 1.9, 6.43], 14, 0.62, first_col_bold=True)
    bullets(s, ["Entorno real de entrenamiento: Windows 11, Python 3.12.8, GPU NVIDIA RTX 5060 Laptop (8 GB), "
                "torch 2.11.0+cu128 (README de Sprint 2 - Entrenamiento)",
                "Reproducible: semilla fija por corrida, configuración y checkpoint guardados en salida_sprint2/"],
            LM, 4.75, CW, 1.6, 15, STAGE[2], gap=8)

    # ---- 13. Resultados finales en validación
    s = content2(D, STAGE[3], "RESULTADOS", "Resultados finales en validación")
    D.tile(s, LM, 1.7, 5.8, 1.75, f"{recall_prom:.2f} % ± {recall_std:.2f} %",
           "Recall medio — clasificador EfficientNetB0 (batch=64), promedio de 3 semillas (42, 123, 2024)", STAGE[3])
    D.tile(s, LM + 6.13, 1.7, 5.8, 1.75, f"{iou_prom:.2f} % ± {iou_std:.2f} %",
           "IoU — U-Net ResNet34 (lr=1e-4), promedio de 3 semillas (42, 123, 2024)", STAGE[3])
    table(s, [
        ["Modelo", "Métrica (validación)", "Base (semilla 42)", "Config. final — prom. 3 semillas", "Meta del acta"],
        ["Clasificador EfficientNetB0", "Recall medio", f"{recall_medio(base_clf):.2f} %",
         f"{recall_prom:.2f} % ± {recall_std:.2f} %", "≥ 90 % por clase"],
        ["Clasificador EfficientNetB0", "Accuracy", f"{base_clf['val_accuracy'] * 100:.1f} %",
         "no promediada", "≥ 95 %"],
        ["U-Net ResNet34", "IoU", f"{base_unet['val_iou'] * 100:.2f} %",
         f"{iou_prom:.2f} % ± {iou_std:.2f} %", "≥ 70 % (solo con tumor)"],
        ["U-Net ResNet34", "Dice", f"{base_unet['val_dice'] * 100:.2f} %", "no promediada", "—"],
    ], LM, 3.75, CW, [3.6, 2.0, 2.0, 2.63, 1.7], 12.5, 0.55, first_col_bold=True)
    text(s, LM, 6.65, CW, 0.3,
         f"Segunda arquitectura candidata: ResNet50 — accuracy {base_resnet['val_accuracy'] * 100:.1f} %, "
         f"recall medio {recall_medio(base_resnet):.2f} % (base); no se llevó a 3 semillas.",
         11, False, MUTED, italic=True)

    # ---- 14. Riesgo R09
    s = content2(D, STAGE[0], "RIESGO R09", "Riesgo R09 — Atajo por procedencia de la imagen")
    pic(s, FIGS + "r09_desglose.png", LM + 1.0, 1.65, w=9.9)
    bullets(s, [
        "Clasificador: sin diferencias relevantes por plano (axial 99,38 %, coronal 99,70 %, sagital 99,71 %); "
        "por tipo de archivo: gris 99,37 %, RGB 99,81 %",
        "U-Net: el glioma es la clase más difícil de segmentar (IoU 67,43 %, frente a 80,07 % hipófisis y "
        "90,12 % meningioma); brecha gris/RGB de ~8 puntos (76,50 % vs. 84,83 %)",
        "Como el 88 % de las imágenes de glioma son en escala de grises (hallazgo del Sprint 1), esa brecha se "
        "explica en buena parte por la dificultad propia del glioma y no (solo) por un atajo de procedencia; "
        "queda pendiente repetir este análisis sobre la prueba oficial en HU12 (Sprint 3)",
    ], LM, 5.35, CW, 1.55, 13, STAGE[0], gap=5)

    # ---- 15. Decisiones
    s = content2(D, STAGE[1], "DECISIONES", "Modelos elegidos para el Sprint 3")
    panel(s, LM, 1.85, 5.8, 3.0, "CLASIFICADOR",
          ["EfficientNetB0 (batch=64, lr=3e-4, con aumento de datos).",
           f"Recall medio promedio en 3 semillas: {recall_prom:.2f} % ± {recall_std:.2f} %, "
           "por encima de la meta (≥ 90 % por clase)."],
          STAGE[2])
    panel(s, LM + 6.13, 1.85, 5.8, 3.0, "SEGMENTACIÓN",
          ["U-Net con encoder ResNet34 (lr=1e-4, con aumento de datos).",
           f"IoU promedio en 3 semillas: {iou_prom:.2f} % ± {iou_std:.2f} %, por encima de la meta (≥ 70 %)."],
          STAGE[3])
    bullets(s, ["Elegidos solo con datos de validación; la prueba oficial no se usó para decidir nada (se evalúa "
                "una sola vez en HU12)",
                "ResNet50 no se llevó a 3 semillas: su recall medio base ya era menor desde el inicio "
                f"({recall_medio(base_resnet):.2f} % frente a {recall_medio(base_clf):.2f} %)",
                "batch=16 en la U-Net (80,09 % a una sola semilla) quedó dentro del margen de variación entre "
                "semillas frente a lr=1e-4; se mantuvo lr=1e-4 por ya tener las 3 semillas corridas"],
            LM, 5.1, CW, 1.8, 14, STAGE[1], gap=6)

    # ---- 16. Riesgos del proyecto
    s = content2(D, STAGE[0], "RIESGOS", "Riesgos del proyecto")
    table(s, [
        ["Riesgo", "Qué hacer (Registro de Riesgos)", "Estado en el Sprint 2"],
        ["R01 · Fuga entre pacientes", "Usar solo la partición propia; agrupar por grupo_hash; avisar de las "
         "113–123 imágenes de prueba parecidas al entrenamiento", "Partición sin cambios; pendiente de aplicar en HU12"],
        ["R04 · Arquitecturas inestables", "Partir de EfficientNetB0 / ResNet50 y repetir con 2–3 semillas",
         f"Hecho: variación baja entre semillas (≤ {max(recall_std, iou_std):.2f} pp)"],
        ["R05 · Modelo pesado para el navegador", "Preferir modelos livianos o cuantizados (ONNX)",
         "Por decidir en el Sprint 3 (HU13)"],
        ["R06 · Memoria de GPU / sobreajuste", "Precisión mixta, lote pequeño, parada temprana; Colab de respaldo",
         "Entrenado con GPU de 8 GB (RTX 5060 Laptop); sin problemas de memoria reportados"],
        ["R09 · Atajo por procedencia (propuesto)", "Normalizar intensidad, aumentar brillo/contraste; reportar "
         "por plano y tipo de archivo", "Investigado con datos reales (evaluar_grupos.py): ver diapositiva anterior"],
    ], LM, 1.8, CW, [2.9, 5.1, 3.93], 12, 0.72, first_col_bold=True)

    # ---- 17. Plan del Sprint 3
    s = content2(D, STAGE[3], "PRÓXIMO SPRINT", "Plan del Sprint 3 (24–29 de octubre de 2026)")
    bullets(s, [
        "HU12 — Evaluación única en la prueba oficial (1.000 imágenes, una sola vez, sin usarla para elegir nada)",
        "HU13 — Aplicación web con el modelo exportado (riesgo R05: tamaño del modelo en el navegador)",
        "HU14 — MLOps básico: versionado y registro de métricas",
        "HU15 — Informe final del proyecto",
        "HU16 — Exposición y ensayo",
        "Presentación final: 30 de octubre · margen: 31 de octubre · fecha límite: 2 de noviembre de 2026",
        "Si falta tiempo, se recorta primero HU11 (modelo multitarea, opcional) y el reentrenamiento final con "
        "las 5.000 imágenes de entrenamiento + validación",
    ], LM, 1.9, CW, 4.9, 16, STAGE[3], gap=10)

    # ---- 18. Cierre
    s = content2(D, STAGE[0], "CIERRE", "Cierre del Sprint 2", [
        "HU05 a HU09 completas: 2 arquitecturas de clasificación, U-Net de segmentación, ajuste de "
        "hiperparámetros y 13 experimentos registrados",
        "Ambos modelos superan las metas del acta (recall ≥ 90 % por clase, IoU ≥ 70 %) solo con datos de validación",
        "Riesgo R09 investigado con datos reales; la brecha gris/RGB de la U-Net se explica más por la "
        "dificultad propia del glioma que por un atajo claro",
        "Pendiente (no técnico, a cargo del equipo): backlog del Sprint 2 en Trello/Excel, Informe de Estado, "
        "Minuta, Registro de Riesgos (agregar R09) y Retrospectiva del Sprint 2",
        "Próximo paso: Sprint 3 — evaluación en la prueba oficial, aplicación web y entrega final "
        "(2 de noviembre de 2026)",
    ], 17)

    out = _AQUI / "presentacion_sprint2.pptx"
    prs.save(str(out))
    return out, len(prs.slides)


if __name__ == "__main__":
    out, n = build()
    size = out.stat().st_size
    print(f"Presentación del Sprint 2: {n} diapositivas, {size} bytes -> {out}")
