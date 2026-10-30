"""HU12 — Evaluacion UNICA sobre la prueba oficial (1.000 imagenes de clasificacion, 860 con mascara).

REGLA DEL PROYECTO (CLAUDE.md): la prueba oficial no se usa para elegir nada; se evalua una sola vez, aqui.
Los modelos evaluados son los FINALES reentrenados sobre train+val y exportados a ONNX (modelos/*.onnx), es decir
exactamente los que sirve la aplicacion web. Se evalua con onnxruntime para que la cifra reportada sea la del
artefacto desplegado.

Reporta, para cada tarea: metrica global, por clase, por plano de corte y por tipo de archivo de origen
(gris/RGB, riesgo R09). Advierte que 113-123 de las 1.000 imagenes de prueba tienen un vecino casi identico en el
entrenamiento oficial (hallazgo del Sprint 1), por lo que la cifra de prueba puede estar algo inflada.

Uso:
    python evaluar_prueba.py
Resultados en salida_sprint3/: evaluacion_prueba.json, figuras y CSV por imagen.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import onnxruntime as ort
import pandas as pd
from PIL import Image

AQUI = Path(__file__).resolve().parent
S1 = AQUI.parent / "Sprint 1 - Notebooks"
S2 = AQUI.parent / "Sprint 2 - Entrenamiento"
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(S2))
from preprocesado import CLASES, CLASES_ES, preprocesar, sigmoide, softmax  # noqa: E402

REGISTRO = AQUI / "modelos"
SALIDA = AQUI / "salida_sprint3"
PERFIL = S1 / "salida_sprint1" / "perfil_datos" / "perfil_imagenes.csv"
NAVY, BLUE, TEAL, GREEN, GRAY = "#1F3864", "#5B84B1", "#2B7A8B", "#8FB89A", "#9AA5B1"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
PLANO_ES = {"ax": "Axial", "co": "Coronal", "sa": "Sagital"}


def raiz_preparado():
    import os
    return Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))


def sesion(nombre):
    provs = ort.get_available_providers()
    prov = ["CUDAExecutionProvider", "CPUExecutionProvider"] if "CUDAExecutionProvider" in provs else ["CPUExecutionProvider"]
    return ort.InferenceSession(str(REGISTRO / f"{nombre}.onnx"), providers=prov)


def tabla_modo():
    if not PERFIL.exists():
        return {}
    p = pd.read_csv(PERFIL)
    p["archivo"] = p.filename.str.rsplit(".", n=1).str[0]
    return p.set_index("archivo")["mode"].to_dict()


def metricas_clasificacion(y_real, y_pred):
    y_real, y_pred = np.asarray(y_real), np.asarray(y_pred)
    n = len(CLASES)
    mat = np.zeros((n, n), dtype=int)
    for r, p in zip(y_real, y_pred):
        mat[r, p] += 1
    acc = float((y_real == y_pred).mean())
    recalls, f1s = {}, []
    for i, c in enumerate(CLASES):
        tp = mat[i, i]; fn = mat[i].sum() - tp; fp = mat[:, i].sum() - tp
        rec = tp / (tp + fn) if tp + fn else 0.0
        prec = tp / (tp + fp) if tp + fp else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        recalls[c] = rec; f1s.append(f1)
    return dict(accuracy=acc, recall_por_clase=recalls, f1_macro=float(np.mean(f1s)), matriz=mat.tolist())


def iou_dice(pred, real, eps=1e-6):
    inter = (pred * real).sum()
    union = pred.sum() + real.sum() - inter
    return float((inter + eps) / (union + eps)), float((2 * inter + eps) / (pred.sum() + real.sum() + eps))


def evaluar():
    SALIDA.mkdir(exist_ok=True)
    raiz = raiz_preparado()
    man = pd.read_csv(raiz / "manifest_preparado.csv")
    test = man[man.particion == "test"].reset_index(drop=True)
    modo = tabla_modo()
    print(f"Prueba oficial: {len(test)} imagenes de clasificacion, {int(test.tiene_mascara.sum())} con mascara")

    # ---------------- clasificacion ----------------
    s_clf = sesion("clasificador_final")
    filas_clf = []
    for r in test.itertuples():
        with Image.open(raiz / r.ruta_imagen) as im:
            x, _ = preprocesar(im)
        logits = s_clf.run(None, {"entrada": x})[0][0]
        pred = int(logits.argmax())
        filas_clf.append(dict(archivo=r.archivo, real=CLASES.index(r.clase), pred=pred,
                              plano=r.plano, modo=modo.get(r.archivo, "?"),
                              confianza=float(softmax(logits).max())))
    dfc = pd.DataFrame(filas_clf)
    met_clf = metricas_clasificacion(dfc.real, dfc.pred)
    print(f"\nCLASIFICACION — accuracy global en prueba: {met_clf['accuracy']*100:.2f}%")
    for c, v in met_clf["recall_por_clase"].items():
        print(f"  recall {c}: {v*100:.2f}%")

    # ---------------- segmentacion ----------------
    s_seg = sesion("unet_final")
    seg = test[test.tiene_mascara].reset_index(drop=True)
    filas_seg = []
    for r in seg.itertuples():
        with Image.open(raiz / r.ruta_imagen) as im:
            x, _ = preprocesar(im)
        logits = s_seg.run(None, {"entrada": x})[0][0, 0]
        pred = (sigmoide(logits) > 0.5).astype(np.float32)
        with Image.open(raiz / r.ruta_mascara) as mk:
            real = (np.asarray(mk) > 127).astype(np.float32)
        iou, dice = iou_dice(pred, real)
        filas_seg.append(dict(archivo=r.archivo, clase=r.clase, plano=r.plano,
                              modo=modo.get(r.archivo, "?"), iou=iou, dice=dice))
    dfs = pd.DataFrame(filas_seg)
    print(f"\nSEGMENTACION — IoU global en prueba: {dfs.iou.mean()*100:.2f}%  Dice: {dfs.dice.mean()*100:.2f}%")

    # ---------------- desgloses ----------------
    def por(df, col, metrica):
        g = df.groupby(col)[metrica].mean()
        n = df.groupby(col)[metrica].count()
        return {str(k): dict(valor=float(g[k]), n=int(n[k])) for k in g.index}

    resultado = dict(
        fecha="2026-10-30", n_test_clasificacion=len(test), n_test_segmentacion=len(seg),
        advertencia=("113-123 de las 1.000 imagenes de prueba tienen un vecino casi identico en el entrenamiento "
                     "oficial (dHash/correlacion, Sprint 1); como el modelo final se reentreno con train+val, la "
                     "cifra de prueba puede estar algo inflada. La prueba oficial se evaluo una sola vez (HU12)."),
        clasificacion=dict(
            accuracy=met_clf["accuracy"], recall_por_clase=met_clf["recall_por_clase"],
            f1_macro=met_clf["f1_macro"], matriz_confusion=met_clf["matriz"],
            accuracy_por_plano=por(dfc.assign(ok=(dfc.real == dfc.pred).astype(float)), "plano", "ok"),
            accuracy_por_modo=por(dfc.assign(ok=(dfc.real == dfc.pred).astype(float)), "modo", "ok"),
        ),
        segmentacion=dict(
            iou=float(dfs.iou.mean()), dice=float(dfs.dice.mean()),
            iou_por_clase=por(dfs, "clase", "iou"), dice_por_clase=por(dfs, "clase", "dice"),
            iou_por_plano=por(dfs, "plano", "iou"), iou_por_modo=por(dfs, "modo", "iou"),
        ),
        metas_acta=dict(accuracy=0.95, recall_por_clase=0.90, iou=0.70),
    )
    (SALIDA / "evaluacion_prueba.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    dfc.to_csv(SALIDA / "prueba_clasificacion_por_imagen.csv", index=False)
    dfs.to_csv(SALIDA / "prueba_segmentacion_por_imagen.csv", index=False)

    _figuras(met_clf, dfc, dfs)
    print("\nResultados en:", SALIDA)
    return resultado


def _figuras(met_clf, dfc, dfs):
    # matriz de confusion en prueba
    mat = np.array(met_clf["matriz"])
    fig, ax = plt.subplots(figsize=(4.8, 4.4))
    im = ax.imshow(mat, cmap="Blues")
    n = len(CLASES)
    ax.set_xticks(range(n)); ax.set_yticks(range(n))
    ax.set_xticklabels([CLASES_ES[c] for c in CLASES], rotation=30, ha="right")
    ax.set_yticklabels([CLASES_ES[c] for c in CLASES])
    ax.set_xlabel("Predicho"); ax.set_ylabel("Real")
    for i in range(n):
        for j in range(n):
            ax.text(j, i, str(mat[i, j]), ha="center", va="center",
                    color="white" if mat[i, j] > mat.max() / 2 else "black", fontsize=10)
    ax.set_title(f"Matriz de confusion — prueba oficial (n={int(mat.sum())})", fontsize=10)
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout(); fig.savefig(SALIDA / "prueba_matriz_confusion.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # IoU por clase en prueba
    g = dfs.groupby("clase")[["iou", "dice"]].mean().reindex(["glioma", "meningioma", "pituitary"])
    x = np.arange(len(g)); w = 0.35
    fig, ax = plt.subplots(figsize=(6.2, 4))
    ax.bar(x - w / 2, g.iou * 100, w, color=NAVY, label="IoU")
    ax.bar(x + w / 2, g.dice * 100, w, color=TEAL, label="Dice")
    for i, (a, b) in enumerate(zip(g.iou, g.dice)):
        ax.text(i - w / 2, a * 100 + 1, f"{a*100:.1f}", ha="center", fontsize=9)
        ax.text(i + w / 2, b * 100 + 1, f"{b*100:.1f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([CLASES_ES[c] for c in g.index])
    ax.set_ylim(0, 100); ax.set_ylabel("%")
    ax.set_title("U-Net — IoU y Dice por clase en la prueba oficial", fontsize=11)
    ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(SALIDA / "prueba_iou_por_clase.png", dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    evaluar()
