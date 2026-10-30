"""Aplicacion web de demostracion — prototipo de sistema clinico (docs/PLAN_SPRINT3.md, HU13).

NO es una herramienta de diagnostico. Es una demostracion academica de apoyo al diagnostico en neuro-oncologia.
Flujo principal real (inicio de sesion -> casos -> subir T1 -> resultado -> revision del medico -> informe); los
demas modulos son maqueta. Inferencia con ONNX Runtime en CPU; funciona sin internet (fuentes del sistema, nada
de CDN). Pacientes y usuarios ficticios; no se guardan datos de pacientes reales.

Uso:
    cd "03. Implementacion/Sprint 3 - Evaluacion y despliegue"
    ../../.venv/Scripts/python.exe -m uvicorn app.servidor:app --port 8000
Abrir http://localhost:8000  (usuario: medico / clave: medico123  ·  admin / admin123)
"""
import io
import json
import os
import sys
from pathlib import Path

from fastapi import FastAPI, Form, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import basedatos as bd  # noqa: E402
from inferencia import predecir, VERSION_MODELOS, UMBRAL_CONFIANZA  # noqa: E402

ESTATICO = AQUI / "estatico"
DEMO = AQUI / "datos_demo" / "imagenes"
MODULOS = {
    "pacientes": "Pacientes", "agenda": "Agenda", "laboratorio": "Laboratorio",
    "imagenologia": "Imagenología general", "facturacion": "Facturación",
    "reportes": "Reportes", "configuracion": "Configuración",
}
AVISO = "Demostración académica. Apoyo al diagnóstico, no es un diagnóstico médico."

app = FastAPI(title="Sistema clínico (demostración académica)")
plantillas = Jinja2Templates(directory=str(AQUI / "plantillas"))
plantillas.env.globals.update(AVISO=AVISO, MODULOS=MODULOS, VERSION_MODELOS=VERSION_MODELOS,
                              UMBRAL=int(UMBRAL_CONFIANZA * 100))


def _preparar_demo():
    """Copia 5-6 imagenes de VALIDACION (no de prueba) como ejemplos; carpeta ignorada por Git."""
    if DEMO.exists() and list(DEMO.glob("*.png")):
        return
    import pandas as pd
    raiz = Path(os.environ.get("BRISC_PREPARADO", Path.home() / "datasets" / "brisc2025_preparado"))
    man_path = raiz / "manifest_preparado.csv"
    if not man_path.exists():
        return
    DEMO.mkdir(parents=True, exist_ok=True)
    man = pd.read_csv(man_path)
    val = man[man.particion == "val"]
    plan = [("glioma", 2), ("meningioma", 1), ("pituitary", 1), ("no_tumor", 1)]  # 5 ejemplos variados
    n = 0
    for clase, k in plan:
        for i, r in enumerate(val[val.clase == clase].head(k).itertuples()):
            try:
                Image.open(raiz / r.ruta_imagen).save(DEMO / f"{n:02d}_{clase}.png")
                n += 1
            except Exception:
                pass


def _usuario(request):
    u = request.cookies.get("sesion")
    if not u:
        return None
    con = bd.conectar()
    r = con.execute("SELECT usuario,nombre,rol FROM usuarios WHERE usuario=?", (u,)).fetchone()
    con.close()
    return dict(r) if r else None


def _ctx(request, **extra):
    return {"request": request, "usuario": _usuario(request), **extra}


@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):
    return RedirectResponse("/casos" if _usuario(request) else "/login")


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return plantillas.TemplateResponse(request, "login.html", _ctx(request, error=None))


@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, usuario: str = Form(...), clave: str = Form(...)):
    u = bd.verificar_usuario(usuario, clave)
    if not u:
        return plantillas.TemplateResponse(request, "login.html", _ctx(request, error="Usuario o clave incorrectos."))
    resp = RedirectResponse("/casos", status_code=303)
    resp.set_cookie("sesion", u["usuario"], httponly=True, samesite="lax")
    return resp


@app.get("/salir")
async def salir():
    resp = RedirectResponse("/login", status_code=303)
    resp.delete_cookie("sesion")
    return resp


@app.get("/casos", response_class=HTMLResponse)
async def casos(request: Request):
    if not _usuario(request):
        return RedirectResponse("/login")
    return plantillas.TemplateResponse(request, "casos.html", _ctx(request, pacientes=bd.pacientes()))


@app.get("/caso/{pid}", response_class=HTMLResponse)
async def caso(request: Request, pid: int):
    if not _usuario(request):
        return RedirectResponse("/login")
    p, estudios = bd.paciente(pid)
    return plantillas.TemplateResponse(request, "caso.html", _ctx(request, paciente=p, estudios=estudios))


@app.get("/caso/{pid}/estudio", response_class=HTMLResponse)
async def estudio_form(request: Request, pid: int):
    if not _usuario(request):
        return RedirectResponse("/login")
    p, _ = bd.paciente(pid)
    ejemplos = sorted(f.name for f in DEMO.glob("*.png")) if DEMO.exists() else []
    return plantillas.TemplateResponse(request, "estudio.html", _ctx(request, paciente=p, ejemplos=ejemplos))


@app.post("/caso/{pid}/estudio", response_class=HTMLResponse)
async def estudio_post(request: Request, pid: int, archivo: UploadFile = File(None), ejemplo: str = Form(None)):
    if not _usuario(request):
        return RedirectResponse("/login")
    nombre, datos = None, None
    if ejemplo:
        ruta = DEMO / ejemplo
        if ruta.exists():
            nombre, datos = ejemplo, ruta.read_bytes()
    elif archivo and archivo.filename:
        nombre, datos = archivo.filename, await archivo.read()
    if not datos:
        p, _ = bd.paciente(pid)
        ejemplos = sorted(f.name for f in DEMO.glob("*.png")) if DEMO.exists() else []
        return plantillas.TemplateResponse(request, "estudio.html",
            _ctx(request, paciente=p, ejemplos=ejemplos, error="Selecciona una imagen (PNG o JPG) o un ejemplo."))
    try:
        im = Image.open(io.BytesIO(datos))
        pred = predecir(im)
    except Exception:
        p, _ = bd.paciente(pid)
        ejemplos = sorted(f.name for f in DEMO.glob("*.png")) if DEMO.exists() else []
        return plantillas.TemplateResponse(request, "estudio.html",
            _ctx(request, paciente=p, ejemplos=ejemplos, error="No se pudo leer la imagen. Usa un PNG o JPG válido."))
    eid = bd.guardar_estudio(pid, nombre, pred)
    return RedirectResponse(f"/resultado/{eid}", status_code=303)


@app.get("/resultado/{eid}", response_class=HTMLResponse)
async def resultado(request: Request, eid: int):
    if not _usuario(request):
        return RedirectResponse("/login")
    e, p = bd.estudio(eid)
    if not e:
        return RedirectResponse("/casos")
    e["probabilidades"] = json.loads(e["probabilidades"]) if e["probabilidades"] else {}
    return plantillas.TemplateResponse(request, "resultado.html", _ctx(request, e=e, paciente=p))


@app.post("/resultado/{eid}/revision", response_class=HTMLResponse)
async def revision(request: Request, eid: int, decision: str = Form(...), clase: str = Form(None),
                   comentario: str = Form("")):
    u = _usuario(request)
    if not u:
        return RedirectResponse("/login")
    e, _ = bd.estudio(eid)
    estado = "aceptado" if decision == "aceptar" else "corregido"
    clase_final = e["clase_es"] if decision == "aceptar" else (clase or "")
    bd.guardar_revision(eid, estado, clase_final, comentario, u["nombre"])
    return RedirectResponse(f"/resultado/{eid}", status_code=303)


@app.get("/informe/{eid}", response_class=HTMLResponse)
async def informe(request: Request, eid: int):
    if not _usuario(request):
        return RedirectResponse("/login")
    e, p = bd.estudio(eid)
    if not e:
        return RedirectResponse("/casos")
    e["probabilidades"] = json.loads(e["probabilidades"]) if e["probabilidades"] else {}
    return plantillas.TemplateResponse(request, "informe.html", _ctx(request, e=e, paciente=p))


@app.get("/ficha-modelo", response_class=HTMLResponse)
async def ficha_modelo(request: Request):
    if not _usuario(request):
        return RedirectResponse("/login")
    registro = {}
    rpath = AQUI.parent / "registro_modelos.json"
    if rpath.exists():
        registro = json.loads(rpath.read_text(encoding="utf-8"))
    return plantillas.TemplateResponse(request, "ficha_modelo.html", _ctx(request, registro=registro))


@app.get("/modulo/{nombre}", response_class=HTMLResponse)
async def modulo(request: Request, nombre: str):
    if not _usuario(request):
        return RedirectResponse("/login")
    return plantillas.TemplateResponse(request, "modulo_maqueta.html",
        _ctx(request, titulo=MODULOS.get(nombre, "Módulo"), clave=nombre))


@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    u = _usuario(request)
    if not u:
        return RedirectResponse("/login")
    return plantillas.TemplateResponse(request, "admin.html", _ctx(request, m=bd.metricas_monitoreo()))


@app.get("/acerca", response_class=HTMLResponse)
async def acerca(request: Request):
    if not _usuario(request):
        return RedirectResponse("/login")
    return plantillas.TemplateResponse(request, "acerca.html", _ctx(request))


@app.get("/demo-imagen/{nombre}")
async def demo_imagen(nombre: str):
    ruta = (DEMO / nombre).resolve()
    if ruta.parent == DEMO.resolve() and ruta.exists():
        return FileResponse(ruta)
    return RedirectResponse("/casos")


bd.iniciar()
_preparar_demo()
app.mount("/estatico", StaticFiles(directory=str(ESTATICO)), name="estatico")
