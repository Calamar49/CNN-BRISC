"""Ejecuta los dos notebooks del Sprint 1 (HU02 y HU03) en orden.

Uso:
    python ejecutar_sprint1.py

Resultados:
    salida_sprint1/                      figuras, eda_resumen.json, particion/, lote_de_prueba.png
    salida_sprint1/notebooks_ejecutados/ copias de los notebooks con todos los resultados (para revisarlos o presentarlos)
"""
import os
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
PROYECTO = AQUI.parents[1]
SALIDA = AQUI / "salida_sprint1"
NOTEBOOKS = ["01_HU02_EDA_BRISC.ipynb", "02_HU03_particion_y_cargador.ipynb"]


def hay_dataset():
    manual = os.environ.get("BRISC_ROOT")
    for b in ([Path(manual)] if manual else []) + [Path.home() / "datasets", PROYECTO / "data"]:
        for _, dn, _ in os.walk(b):
            if any(d.lower().replace("_", " ") == "classification task" for d in dn):
                return True
    return False


def main():
    if not hay_dataset():
        print("No encuentro el dataset en", Path.home() / "datasets", "ni en", PROYECTO / "data")
        print("Ejecuta primero:  python descargar_brisc.py")
        print("(o define la variable de entorno BRISC_ROOT con la carpeta que contiene 'classification task')")
        return 1
    (SALIDA / "notebooks_ejecutados").mkdir(parents=True, exist_ok=True)
    for nb in NOTEBOOKS:
        print(f"\n=== Ejecutando {nb} ===")
        cmd = [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute",
               "--ExecutePreprocessor.timeout=3600",
               "--output-dir", str(SALIDA / "notebooks_ejecutados"), str(AQUI / nb)]
        r = subprocess.run(cmd, cwd=AQUI)
        if r.returncode != 0:
            print(f"\nFallo {nb}. Abre el notebook en VS Code o Jupyter para ver en que celda se detuvo.")
            return r.returncode
    print("\nListo. Revisa la carpeta:", SALIDA)
    print("Con esos resultados completen las diapositivas 6 y 7 de la Revision del Sprint y el Informe de Estado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
