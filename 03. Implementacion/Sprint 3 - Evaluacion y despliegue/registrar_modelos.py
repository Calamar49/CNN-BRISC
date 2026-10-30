"""HU14 — MLOps basico: registro de modelos versionado y registro de metricas.

Reune en un solo archivo (registro_modelos.json, que SI se sube a Git — no pesa nada) la procedencia de cada
modelo final, su tarjeta de modelo (formato ONNX, tamano, paridad), su metrica de validacion del Sprint 2 y su
metrica en la prueba oficial del Sprint 3 (HU12), y el commit de Git en que se genero. Los pesos y los .onnx NO
se suben (los regenera reentrenar_final.py + exportar_onnx.py); el registro es la parte reproducible y auditable.

Uso (tras reentrenar, exportar y evaluar):
    python registrar_modelos.py
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REGISTRO = AQUI / "modelos"
SALIDA = AQUI / "salida_sprint3"


def git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(AQUI),
                              capture_output=True, text=True).stdout.strip() or "sin-commit"
    except Exception:
        return "sin-commit"


def cargar(p, defecto=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else (defecto or {})


def main():
    evalu = cargar(SALIDA / "evaluacion_prueba.json")
    clf_card = cargar(REGISTRO / "clasificador_final_tarjeta.json")
    unet_card = cargar(REGISTRO / "unet_final_tarjeta.json")

    # metricas de validacion (Sprint 2, promedio de las 3 semillas de la config elegida) — del README de Sprint 2
    val = {"clasificador_final": {"metrica": "recall medio", "validacion": "99.57% ± 0.12% (3 semillas, Sprint 2)"},
           "unet_final": {"metrica": "IoU", "validacion": "80.12% ± 0.27% (3 semillas, Sprint 2)"}}

    clf_prueba = evalu.get("clasificacion", {})
    seg_prueba = evalu.get("segmentacion", {})

    registro = {
        "proyecto": "BRISC 2025 — clasificacion y segmentacion de tumores cerebrales",
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "commit_git": git_commit(),
        "nota": ("Demostracion academica, no herramienta de diagnostico. Los pesos (.pt) y los modelos (.onnx) no "
                 "se versionan en Git; se regeneran con reentrenar_final.py + exportar_onnx.py. La prueba oficial "
                 "se evaluo una sola vez (HU12)."),
        "modelos": [
            {
                "nombre": "clasificador_final", "tarea": "clasificacion",
                "arquitectura": "EfficientNetB0 (transfer learning ImageNet)",
                "entrenamiento": clf_card.get("entrenamiento", {}),
                "artefacto": {k: clf_card.get(k) for k in ("archivo", "formato", "tamano_mb", "paridad_pytorch_onnx")},
                "validacion_sprint2": val["clasificador_final"]["validacion"],
                "prueba_oficial_hu12": {
                    "accuracy": round(clf_prueba.get("accuracy", 0) * 100, 2) if clf_prueba else None,
                    "recall_por_clase": {k: round(v * 100, 2) for k, v in clf_prueba.get("recall_por_clase", {}).items()},
                    "f1_macro": round(clf_prueba.get("f1_macro", 0) * 100, 2) if clf_prueba else None,
                },
            },
            {
                "nombre": "unet_final", "tarea": "segmentacion",
                "arquitectura": "U-Net con encoder ResNet34 (transfer learning ImageNet)",
                "entrenamiento": unet_card.get("entrenamiento", {}),
                "artefacto": {k: unet_card.get(k) for k in ("archivo", "formato", "tamano_mb", "paridad_pytorch_onnx")},
                "validacion_sprint2": val["unet_final"]["validacion"],
                "prueba_oficial_hu12": {
                    "iou": round(seg_prueba.get("iou", 0) * 100, 2) if seg_prueba else None,
                    "dice": round(seg_prueba.get("dice", 0) * 100, 2) if seg_prueba else None,
                    "iou_por_clase": {k: round(v["valor"] * 100, 2) for k, v in seg_prueba.get("iou_por_clase", {}).items()},
                },
            },
        ],
        "metas_acta": {"accuracy": ">= 95%", "recall_por_clase": ">= 90%", "iou": ">= 70%"},
    }
    ruta = AQUI / "registro_modelos.json"
    ruta.write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Registro de modelos escrito en:", ruta)
    for m in registro["modelos"]:
        print(f"  {m['nombre']}: val {m['validacion_sprint2']} | prueba {m['prueba_oficial_hu12']}")


if __name__ == "__main__":
    main()
