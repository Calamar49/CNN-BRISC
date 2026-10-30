"""HU14 — MLOps basico: registro de modelos y de datos versionado (docs/PLAN_SPRINT3.md seccion 7).

Reune en registro_modelos.json (se sube a Git; no pesa nada) la procedencia de cada modelo DESPLEGADO (semilla
2024 del Sprint 2), su SHA-256, tamano y versiones de librerias, su metrica de validacion (Sprint 2, 3 semillas)
y su metrica en la prueba oficial (Sprint 3, HU12), la version del dataset (SHA-256 del manifest + semilla 42) y
el commit de Git. Los pesos (.pt) y los modelos (.onnx) NO se suben; se regeneran con reentrenar/exportar.

El monitoreo de predicciones en produccion se hace en la propia aplicacion (app/basedatos.py, tabla predicciones,
y la pagina /admin), sin guardar imagenes ni datos personales.

Uso (tras exportar y evaluar):  python registrar_modelos.py
"""
import hashlib
import json
import os
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


def sha256(ruta):
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cargar(p, d=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else (d or {})


def main():
    evalu = cargar(SALIDA / "evaluacion_prueba.json")
    clf = cargar(REGISTRO / "clasificador_v1_tarjeta.json")
    seg = cargar(REGISTRO / "segmentacion_v1_tarjeta.json")
    c = evalu.get("clasificacion", {})
    s = evalu.get("segmentacion", {})

    # version del dataset
    raiz = Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))
    manifest = raiz / "manifest_preparado.csv"
    dataset = dict(nombre="BRISC 2025 preparado", semilla_particion=42,
                   particion="3999 train / 1001 val / 1000 test",
                   sha256_manifest=sha256(manifest) if manifest.exists() else "n/d (regenerar con el Sprint 1)")

    def bloque(nombre, card, tarea, val, prueba):
        return dict(
            nombre=nombre, tarea=tarea, arquitectura=card.get("salida", ""),
            artefacto={k: card.get(k) for k in ("archivo", "formato", "tamano_mb", "sha256", "punto_de_control",
                                                "paridad_pytorch_onnx")},
            versiones=card.get("versiones", {}), validacion_sprint2=val, prueba_oficial_hu12=prueba,
            etiqueta_git=f"modelo-{nombre}-v1.0",
        )

    registro = dict(
        proyecto="BRISC 2025 — clasificacion y segmentacion de tumores cerebrales",
        generado=datetime.now().strftime("%Y-%m-%d %H:%M"), commit_git=git_commit(),
        nota=("Demostracion academica, no herramienta de diagnostico. Modelos desplegados = mejores por validacion "
              "del Sprint 2 (semilla 2024). Los pesos (.pt) y los .onnx no se versionan en Git; se regeneran con "
              "exportar_onnx.py. La prueba oficial se evaluo una sola vez (HU12). Monitoreo en la app (/admin)."),
        dataset=dataset,
        modelos=[
            bloque("clasificador", clf, "clasificacion",
                   "recall medio 99.57% ± 0.15% (3 semillas)",
                   dict(accuracy=round(c.get("desplegado", {}).get("accuracy", 0) * 100, 2),
                        recall_por_clase={k: round(v * 100, 2) for k, v in c.get("desplegado", {}).get("recall_por_clase", {}).items()},
                        promedio_3_semillas=f"accuracy {round(c.get('accuracy_promedio',0)*100,2)}% ± {round(c.get('accuracy_desvio',0)*100,2)}%")),
            bloque("segmentacion", seg, "segmentacion",
                   "IoU 80.12% ± 0.33% (3 semillas)",
                   dict(iou=round(s.get("desplegado", {}).get("iou", 0) * 100, 2),
                        dice=round(s.get("desplegado", {}).get("dice", 0) * 100, 2),
                        iou_por_clase={k: round(v["valor"] * 100, 2) for k, v in s.get("desplegado", {}).get("iou_por_clase", {}).items()},
                        promedio_3_semillas=f"IoU {round(s.get('iou_promedio',0)*100,2)}% ± {round(s.get('iou_desvio',0)*100,2)}%")),
        ],
        metas_acta={"accuracy": ">= 95%", "recall_por_clase": ">= 90%", "iou": ">= 70%"},
        cumple_metas=evalu.get("cumple", {}),
        etiquetas_git=["datos-v1.0", "modelo-clasificador-v1.0", "modelo-segmentacion-v1.0", "app-v1.0"],
    )
    (AQUI / "registro_modelos.json").write_text(json.dumps(registro, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Registro escrito en registro_modelos.json  (commit", registro["commit_git"] + ")")
    for m in registro["modelos"]:
        print(f"  {m['nombre']}: val {m['validacion_sprint2']} | prueba {m['prueba_oficial_hu12']}")


if __name__ == "__main__":
    main()
