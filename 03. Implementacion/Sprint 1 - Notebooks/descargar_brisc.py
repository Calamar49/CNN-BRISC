"""Descarga y descomprime el dataset BRISC 2025 en ~/datasets/ (carpeta "datasets" de tu usuario)

Uso:
    python descargar_brisc.py

Requisitos: tener instalado el CLI de Kaggle (pip install kaggle).
El dataset es publico: normalmente se descarga sin iniciar sesion. Si Kaggle pide autenticacion,
ejecuta una vez  kaggle auth login  (abre el navegador; no hace falta copiar ningun token).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROYECTO = Path(__file__).resolve().parents[2]   # .../sistema-inteligente-tumores-cerebrales
DESTINO = Path.home() / "datasets"   # fuera de OneDrive, para no sincronizar ~15.000 imagenes a la nube
DATASET = "briscdataset/brisc2025"
PAGINA = "https://www.kaggle.com/datasets/briscdataset/brisc2025/"


def hay_dataset():
    for dp, dn, _ in os.walk(DESTINO):
        if any(d.lower().replace("_", " ") == "classification task" for d in dn):
            return Path(dp)
    return None


def main():
    previo = hay_dataset() if DESTINO.exists() else None  # busca en ~/datasets
    if previo:
        print(f"El dataset ya esta en: {previo}\nNo se descarga de nuevo.")
        return 0

    if shutil.which("kaggle") is None:
        print("No encuentro el comando 'kaggle'. Instalalo con:  pip install kaggle")
        print("Alternativa manual: descarga el zip desde", PAGINA, "y descomprimelo dentro de", DESTINO)
        return 1

    DESTINO.mkdir(exist_ok=True)
    print(f"Descargando {DATASET} en {DESTINO} (puede tardar varios minutos)...")
    r = subprocess.run(["kaggle", "datasets", "download", "-d", DATASET, "-p", str(DESTINO), "--unzip"])
    if r.returncode != 0:
        print("\nLa descarga fallo. Si el mensaje habla de autenticacion, ejecuta una vez:")
        print("    kaggle auth login")
        print("(se abre el navegador para iniciar sesion) y vuelve a correr este script.")
        print("Alternativa manual: descarga el zip desde", PAGINA, "y descomprimelo dentro de", DESTINO)
        return r.returncode

    raiz = hay_dataset()
    if raiz is None:
        print("Se descargo, pero no encuentro la carpeta 'classification task'. Revisa el contenido de", DESTINO)
        return 2
    n_img = sum(1 for p in raiz.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    print(f"\nListo. Dataset en: {raiz}\nArchivos de imagen encontrados: {n_img}")
    print("Siguiente paso:  python ejecutar_sprint1.py   (o abre los notebooks en VS Code)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
