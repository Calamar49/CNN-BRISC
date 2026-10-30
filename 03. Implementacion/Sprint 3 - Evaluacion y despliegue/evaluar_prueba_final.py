"""HU12 — Evaluacion UNICA sobre la prueba oficial, siguiendo docs/PLAN_SPRINT3.md (seccion 5).

REGLA DE ORO: la prueba se evalua UNA VEZ. No se cambia nada despues de ver los numeros.
Se evaluan los 6 puntos de control del Sprint 2 (3 semillas por tarea) y se reporta promedio +- desvio (muestral).
El modelo que se DESPLIEGA es el mejor por VALIDACION de cada tarea (semilla 2024 en ambos casos); los desgloses,
la matriz de confusion y el analisis de errores se hacen con ese modelo desplegado.

Produce (en salida_sprint3/):
  - evaluacion_prueba.json  (por semilla, promedio+-desvio, desgloses, cumple/no-cumple, subconjunto sin vecino)
  - test_con_vecino_cercano.csv (las imagenes de prueba con un vecino casi identico en el entrenamiento oficial)
  - prueba_*_por_imagen.csv, figuras y ejemplos visuales de aciertos y errores.

Uso:  python evaluar_prueba_final.py
"""
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from PIL import Image

AQUI = Path(__file__).resolve().parent
S1 = AQUI.parent / "Sprint 1 - Notebooks"
S2 = AQUI.parent / "Sprint 2 - Entrenamiento"
sys.path.insert(0, str(AQUI)); sys.path.insert(0, str(S2))
from preprocesado import CLASES, CLASES_ES, preprocesar  # noqa: E402
from modelos import crear_clasificador, crear_unet  # noqa: E402

SAL2 = S2 / "salida_sprint2"
SALIDA = AQUI / "salida_sprint3"
PERFIL = S1 / "salida_sprint1" / "perfil_datos" / "perfil_imagenes.csv"
NAVY, BLUE, TEAL, GREEN, GRAY = "#1F3864", "#5B84B1", "#2B7A8B", "#8FB89A", "#9AA5B1"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})

# puntos de control del Sprint 2 (de experimentos.csv): config elegida, 3 semillas por tarea
CLF = {42: "clf_efficientnet_b0_20261023_002839", 123: "clf_efficientnet_b0_20261023_004200",
       2024: "clf_efficientnet_b0_20261023_004900"}
UNET = {42: "unet_resnet34_20261023_002334", 123: "unet_resnet34_20261023_005823",
        2024: "unet_resnet34_20261023_005828"}
SEMILLA_DESPLIEGUE = 2024  # el mejor por validacion en ambas tareas


def raiz_preparado():
    return Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))


def tabla_modo():
    if not PERFIL.exists():
        return {}
    p = pd.read_csv(PERFIL)
    p["archivo"] = p.filename.str.rsplit(".", n=1).str[0]
    return p.set_index("archivo")["mode"].to_dict()


def cargar_clasificador(semilla, device):
    ck = torch.load(SAL2 / f"{CLF[semilla]}.pt", map_location=device, weights_only=False)
    m = crear_clasificador(ck["arquitectura"], preentrenado=False).to(device)
    m.load_state_dict(ck["modelo"]); m.eval()
    return m


def cargar_unet(semilla, device):
    ck = torch.load(SAL2 / f"{UNET[semilla]}.pt", map_location=device, weights_only=False)
    m = crear_unet(ck["encoder"], preentrenado=False).to(device)
    m.load_state_dict(ck["modelo"]); m.eval()
    return m


def tensor(raiz, ruta):
    with Image.open(raiz / ruta) as im:
        return torch.from_numpy(preprocesar(im)[0])


def metricas_clf(y_real, y_pred):
    y_real, y_pred = np.asarray(y_real), np.asarray(y_pred)
    n = len(CLASES); mat = np.zeros((n, n), int)
    for r, p in zip(y_real, y_pred):
        mat[r, p] += 1
    acc = float((y_real == y_pred).mean())
    rec, f1 = {}, []
    for i, c in enumerate(CLASES):
        tp = mat[i, i]; fn = mat[i].sum() - tp; fp = mat[:, i].sum() - tp
        r_ = tp / (tp + fn) if tp + fn else 0.0
        p_ = tp / (tp + fp) if tp + fp else 0.0
        rec[c] = r_; f1.append(2 * p_ * r_ / (p_ + r_) if p_ + r_ else 0.0)
    return dict(accuracy=acc, recall_por_clase=rec, f1_macro=float(np.mean(f1)), matriz=mat.tolist())


def iou_dice(pred, real, eps=1e-6):
    inter = (pred * real).sum()
    return (float((inter + eps) / (pred.sum() + real.sum() - inter + eps)),
            float((2 * inter + eps) / (pred.sum() + real.sum() + eps)))


def vecinos_cercanos(raiz, man, umbral=0.98, lado=32):
    """Imagenes de prueba con un vecino casi identico en el entrenamiento oficial (correlacion de miniaturas
    32x32 >= 0.98), como en el notebook 02_HU03. Devuelve el set de archivos de prueba con vecino cercano."""
    def miniaturas(sub):
        M = np.zeros((len(sub), lado * lado), np.float32)
        for i, r in enumerate(sub.itertuples()):
            with Image.open(raiz / r.ruta_imagen) as im:
                a = np.asarray(im.convert("L").resize((lado, lado), Image.BILINEAR), np.float32).ravel()
            a = a - a.mean()
            n = np.linalg.norm(a)
            M[i] = a / n if n > 0 else a
        return M
    tr = man[man.particion_oficial == "train"].reset_index(drop=True)
    te = man[man.particion == "test"].reset_index(drop=True)
    Mtr, Mte = miniaturas(tr), miniaturas(te)
    cercanos = set()
    paso = 200
    for i0 in range(0, len(Mte), paso):
        corr = Mte[i0:i0 + paso] @ Mtr.T  # correlacion (ya z-normalizado y unidad)
        maxc = corr.max(axis=1)
        for j, c in enumerate(maxc):
            if c >= umbral:
                cercanos.add(te.iloc[i0 + j].archivo)
    return cercanos


def evaluar():
    SALIDA.mkdir(exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    raiz = raiz_preparado()
    man = pd.read_csv(raiz / "manifest_preparado.csv")
    test = man[man.particion == "test"].reset_index(drop=True)
    seg = test[test.tiene_mascara].reset_index(drop=True)
    modo = tabla_modo()
    print(f"Dispositivo: {device}. Prueba: {len(test)} clasif, {len(seg)} con mascara")

    # ---- vecino cercano (para el subconjunto honesto)
    print("Buscando vecinos cercanos (miniaturas 32x32, correlacion >= 0.98)...")
    cercanos = vecinos_cercanos(raiz, man)
    pd.DataFrame({"archivo": sorted(cercanos)}).to_csv(SALIDA / "test_con_vecino_cercano.csv", index=False)
    print(f"  {len(cercanos)} imagenes de prueba con vecino casi identico en entrenamiento")

    # ---- CLASIFICACION: 3 semillas
    pred_por_semilla = {}
    acc_semillas, rec_semillas = {}, {}
    with torch.no_grad():
        for s in (42, 123, 2024):
            m = cargar_clasificador(s, device)
            preds, reales, confs = [], [], []
            for r in test.itertuples():
                x = tensor(raiz, r.ruta_imagen).to(device)
                with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                    logits = m(x)[0]
                p = torch.softmax(logits.float(), 0)
                preds.append(int(p.argmax())); reales.append(CLASES.index(r.clase)); confs.append(float(p.max()))
            met = metricas_clf(reales, preds)
            acc_semillas[s] = met["accuracy"]
            rec_semillas[s] = float(np.mean(list(met["recall_por_clase"].values())))
            pred_por_semilla[s] = (reales, preds, confs, met)
            print(f"  clasificador semilla {s}: accuracy {met['accuracy']*100:.2f}%  recall medio {rec_semillas[s]*100:.2f}%")

    # ---- SEGMENTACION: 3 semillas
    iou_semillas, dice_semillas, seg_por_semilla = {}, {}, {}
    with torch.no_grad():
        for s in (42, 123, 2024):
            m = cargar_unet(s, device)
            ious, dices, det = [], [], []
            for r in seg.itertuples():
                x = tensor(raiz, r.ruta_imagen).to(device)
                with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                    logits = m(x)[0, 0]
                pred = (torch.sigmoid(logits.float()) > 0.5).cpu().numpy().astype(np.float32)
                with Image.open(raiz / r.ruta_mascara) as mk:
                    real = (np.asarray(mk) > 127).astype(np.float32)
                i, d = iou_dice(pred, real)
                ious.append(i); dices.append(d)
                det.append(dict(archivo=r.archivo, clase=r.clase, plano=r.plano, modo=modo.get(r.archivo, "?"), iou=i, dice=d))
            iou_semillas[s] = float(np.mean(ious)); dice_semillas[s] = float(np.mean(dices))
            seg_por_semilla[s] = pd.DataFrame(det)
            print(f"  U-Net semilla {s}: IoU {iou_semillas[s]*100:.2f}%  Dice {dice_semillas[s]*100:.2f}%")

    # ---- modelo desplegado (semilla 2024): desgloses y analisis de errores
    reales, preds, confs, met_desp = pred_por_semilla[SEMILLA_DESPLIEGUE]
    dfc = pd.DataFrame(dict(archivo=test.archivo, real=reales, pred=preds, conf=confs,
                            plano=test.plano, modo=[modo.get(a, "?") for a in test.archivo]))
    dfc["ok"] = (dfc.real == dfc.pred).astype(int)
    dfc["vecino_cercano"] = dfc.archivo.isin(cercanos)
    dfc.to_csv(SALIDA / "prueba_clasificacion_por_imagen.csv", index=False)
    dfs = seg_por_semilla[SEMILLA_DESPLIEGUE].copy()
    dfs["vecino_cercano"] = dfs.archivo.isin(cercanos)
    dfs.to_csv(SALIDA / "prueba_segmentacion_por_imagen.csv", index=False)

    # subconjunto SIN vecino cercano
    dfc_sin = dfc[~dfc.vecino_cercano]
    dfs_sin = dfs[~dfs.vecino_cercano]
    met_sin = metricas_clf(dfc_sin.real, dfc_sin.pred)

    def resumen(df, col, metrica):
        g = df.groupby(col)[metrica].mean(); n = df.groupby(col)[metrica].count()
        return {str(k): dict(valor=float(g[k]), n=int(n[k])) for k in g.index}

    prom = lambda d: float(np.mean(list(d.values())))
    desv = lambda d: float(np.std(list(d.values()), ddof=1))
    resultado = dict(
        fecha="2026-10-30", protocolo="docs/PLAN_SPRINT3.md seccion 5",
        n_test_clasificacion=len(test), n_test_segmentacion=len(seg),
        semilla_desplegada=SEMILLA_DESPLIEGUE,
        imagenes_con_vecino_cercano=len(cercanos),
        clasificacion=dict(
            por_semilla={str(s): dict(accuracy=acc_semillas[s], recall_medio=rec_semillas[s]) for s in (42, 123, 2024)},
            accuracy_promedio=prom(acc_semillas), accuracy_desvio=desv(acc_semillas),
            recall_medio_promedio=prom(rec_semillas), recall_medio_desvio=desv(rec_semillas),
            desplegado=dict(accuracy=met_desp["accuracy"], recall_por_clase=met_desp["recall_por_clase"],
                            f1_macro=met_desp["f1_macro"], matriz_confusion=met_desp["matriz"]),
            accuracy_por_plano=resumen(dfc, "plano", "ok"), accuracy_por_modo=resumen(dfc, "modo", "ok"),
            accuracy_sin_vecino=met_sin["accuracy"], n_sin_vecino=len(dfc_sin),
        ),
        segmentacion=dict(
            por_semilla={str(s): dict(iou=iou_semillas[s], dice=dice_semillas[s]) for s in (42, 123, 2024)},
            iou_promedio=prom(iou_semillas), iou_desvio=desv(iou_semillas),
            dice_promedio=prom(dice_semillas), dice_desvio=desv(dice_semillas),
            desplegado=dict(iou=float(dfs.iou.mean()), dice=float(dfs.dice.mean()),
                            iou_por_clase=resumen(dfs, "clase", "iou"), dice_por_clase=resumen(dfs, "clase", "dice"),
                            iou_por_plano=resumen(dfs, "plano", "iou"), iou_por_modo=resumen(dfs, "modo", "iou")),
            iou_sin_vecino=float(dfs_sin.iou.mean()), n_sin_vecino=len(dfs_sin),
        ),
        metas_acta=dict(accuracy=0.95, recall_por_clase=0.90, iou=0.70),
        cumple=dict(
            accuracy=bool(met_desp["accuracy"] >= 0.95),
            recall_por_clase=bool(min(met_desp["recall_por_clase"].values()) >= 0.90),
            iou=bool(float(dfs.iou.mean()) >= 0.70),
        ),
        advertencia=(f"{len(cercanos)} de {len(test)} imagenes de prueba tienen un vecino casi identico en el "
                     "entrenamiento oficial; se reportan aparte las metricas SIN esas imagenes. La prueba oficial "
                     "se evaluo una sola vez (HU12). El modelo desplegado se eligio por validacion (semilla 2024), "
                     "no mirando la prueba."),
        limitaciones=("Sin ID de paciente; solo T1 con contraste; un solo dataset; la prueba difiere moderadamente "
                      "del entrenamiento; posible atajo por procedencia (R09, se reporta por plano y tipo de archivo)."),
    )
    (SALIDA / "evaluacion_prueba.json").write_text(json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")

    _figuras(met_desp, dfc, dfs)
    _ejemplos(raiz, dfc, dfs, cargar_unet(SEMILLA_DESPLIEGUE, device), device)

    print(f"\nCLASIFICACION desplegada (semilla {SEMILLA_DESPLIEGUE}): accuracy {met_desp['accuracy']*100:.2f}% | "
          f"promedio 3 semillas {prom(acc_semillas)*100:.2f}% ± {desv(acc_semillas)*100:.2f}%")
    print(f"SEGMENTACION desplegada: IoU {dfs.iou.mean()*100:.2f}% | promedio {prom(iou_semillas)*100:.2f}% ± {desv(iou_semillas)*100:.2f}%")
    print("Cumple metas:", resultado["cumple"])
    print("Resultados en:", SALIDA)
    return resultado


def _figuras(met, dfc, dfs):
    mat = np.array(met["matriz"]); n = len(CLASES)
    fig, ax = plt.subplots(figsize=(4.8, 4.4))
    im = ax.imshow(mat, cmap="Blues")
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

    g = dfs.groupby("clase")[["iou", "dice"]].mean().reindex(["glioma", "meningioma", "pituitary"])
    x = np.arange(len(g)); w = 0.35
    fig, ax = plt.subplots(figsize=(6.2, 4))
    ax.bar(x - w / 2, g.iou * 100, w, color=NAVY, label="IoU")
    ax.bar(x + w / 2, g.dice * 100, w, color=TEAL, label="Dice")
    for i, (a, b) in enumerate(zip(g.iou, g.dice)):
        ax.text(i - w / 2, a * 100 + 1, f"{a*100:.1f}", ha="center", fontsize=9)
        ax.text(i + w / 2, b * 100 + 1, f"{b*100:.1f}", ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels([CLASES_ES[c] for c in g.index]); ax.set_ylim(0, 100); ax.set_ylabel("%")
    ax.set_title("U-Net — IoU y Dice por clase en la prueba oficial", fontsize=11); ax.legend(frameon=False)
    fig.tight_layout(); fig.savefig(SALIDA / "prueba_iou_por_clase.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def _ejemplos(raiz, dfc, dfs, unet, device):
    """4-6 ejemplos visuales de aciertos y errores (clasificacion y segmentacion)."""
    rng = np.random.RandomState(42)
    aciertos = dfc[dfc.ok == 1]
    errores = dfc[dfc.ok == 0]
    muestra = pd.concat([aciertos.sample(min(3, len(aciertos)), random_state=1),
                         errores.sample(min(3, len(errores)), random_state=1)]) if len(errores) else aciertos.sample(min(6, len(aciertos)), random_state=1)
    man = pd.read_csv(raiz / "manifest_preparado.csv").set_index("archivo")
    fig, ejes = plt.subplots(1, len(muestra), figsize=(2.3 * len(muestra), 2.8))
    if len(muestra) == 1:
        ejes = [ejes]
    for ax, r in zip(ejes, muestra.itertuples()):
        with Image.open(raiz / man.loc[r.archivo].ruta_imagen) as im:
            ax.imshow(np.asarray(im.convert("L")), cmap="gray")
        ok = r.ok == 1
        ax.set_title(f"{'OK' if ok else 'ERROR'}\nreal {CLASES_ES[CLASES[r.real]]}\npred {CLASES_ES[CLASES[r.pred]]} ({r.conf*100:.0f}%)",
                     fontsize=8, color=(NAVY if ok else "#b5651d"))
        ax.axis("off")
    fig.suptitle("Clasificacion — aciertos y errores en la prueba oficial", fontsize=10)
    fig.tight_layout(); fig.savefig(SALIDA / "prueba_ejemplos_clasificacion.png", dpi=150, bbox_inches="tight"); plt.close(fig)

    # segmentacion: 2 mejores y 2 peores por IoU
    peores = dfs.nsmallest(2, "iou"); mejores = dfs.nlargest(2, "iou")
    sel = pd.concat([mejores, peores])
    fig, ejes = plt.subplots(len(sel), 3, figsize=(7, 2.3 * len(sel)))
    with torch.no_grad():
        for fila, r in enumerate(sel.itertuples()):
            with Image.open(raiz / man.loc[r.archivo].ruta_imagen) as im:
                x = torch.from_numpy(preprocesar(im)[0]).to(device)
                gris = np.asarray(im.convert("L").resize((256, 256)))
            with Image.open(raiz / man.loc[r.archivo].ruta_mascara) as mk:
                real = (np.asarray(mk) > 127)
            logits = unet(x)[0, 0]
            pred = (torch.sigmoid(logits.float()) > 0.5).cpu().numpy()
            ejes[fila, 0].imshow(gris, cmap="gray"); ejes[fila, 0].set_title("imagen", fontsize=8); ejes[fila, 0].axis("off")
            ejes[fila, 1].imshow(real, cmap="gray"); ejes[fila, 1].set_title("mascara real", fontsize=8); ejes[fila, 1].axis("off")
            ejes[fila, 2].imshow(pred, cmap="gray"); ejes[fila, 2].set_title(f"predicha (IoU {r.iou*100:.0f}%)", fontsize=8); ejes[fila, 2].axis("off")
    fig.suptitle("Segmentacion — 2 mejores y 2 peores por IoU (prueba oficial)", fontsize=10)
    fig.tight_layout(); fig.savefig(SALIDA / "prueba_ejemplos_segmentacion.png", dpi=150, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    evaluar()
