"""Base de datos SQLite de la demostracion (docs/PLAN_SPRINT3.md). Guarda usuarios y pacientes FICTICIOS,
los estudios realizados y un registro de predicciones para el monitoreo basico (HU14).

Privacidad (plan seccion 15.2): el registro de monitoreo NO guarda la imagen subida ni datos personales; solo
metricas agregadas de la prediccion. Los pacientes son inventados y estan marcados como ficticios. Las claves se
guardan con hash (no en texto plano); es una demostracion, no seguridad real.
"""
import hashlib
import os
import sqlite3
from datetime import datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
BD = AQUI / "datos_demo" / "demo.sqlite"
SAL = "brisc-demo-academica"  # sal fija: es una demo, no seguridad real

PACIENTES_FICTICIOS = [
    ("NEO-0001", "Paciente ficticio A", 54, "F", "Cefalea persistente. Estudio de control."),
    ("NEO-0002", "Paciente ficticio B", 43, "M", "Hallazgo incidental en TC previa."),
    ("NEO-0003", "Paciente ficticio C", 61, "F", "Seguimiento post-operatorio."),
    ("NEO-0004", "Paciente ficticio D", 37, "M", "Crisis convulsiva de reciente aparicion."),
    ("NEO-0005", "Paciente ficticio E", 29, "F", "Alteraciones visuales; descartar lesion selar."),
    ("NEO-0006", "Paciente ficticio F", 68, "M", "Deterioro cognitivo en estudio."),
]
USUARIOS = [
    ("medico", "Dra. Médico de demostración", "medico", "medico123"),
    ("admin", "Administrador de demostración", "admin", "admin123"),
]


def hash_clave(clave):
    return hashlib.sha256((SAL + clave).encode()).hexdigest()


def conectar():
    con = sqlite3.connect(BD)
    con.row_factory = sqlite3.Row
    return con


def iniciar():
    BD.parent.mkdir(parents=True, exist_ok=True)
    con = conectar()
    c = con.cursor()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY, usuario TEXT UNIQUE, nombre TEXT, rol TEXT, clave_hash TEXT);
    CREATE TABLE IF NOT EXISTS pacientes (
        id INTEGER PRIMARY KEY, codigo TEXT UNIQUE, nombre TEXT, edad INTEGER, sexo TEXT, notas TEXT);
    CREATE TABLE IF NOT EXISTS estudios (
        id INTEGER PRIMARY KEY, paciente_id INTEGER, fecha TEXT, archivo_nombre TEXT,
        clase_predicha TEXT, clase_es TEXT, confianza REAL, confianza_baja INTEGER, area_pct REAL,
        version_modelos TEXT, imagen_b64 TEXT, mascara_b64 TEXT, probabilidades TEXT,
        revision_estado TEXT DEFAULT 'pendiente', revision_clase TEXT, revision_comentario TEXT,
        revision_medico TEXT, revision_fecha TEXT);
    CREATE TABLE IF NOT EXISTS predicciones (
        id INTEGER PRIMARY KEY, fecha TEXT, version_modelos TEXT, clase TEXT,
        prob_glioma REAL, prob_meningioma REAL, prob_pituitary REAL, prob_no_tumor REAL,
        confianza REAL, confianza_baja INTEGER, area_pct REAL, tiempo_ms REAL, brillo_medio REAL);
    """)
    if not c.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone():
        for u, nom, rol, clave in USUARIOS:
            c.execute("INSERT INTO usuarios(usuario,nombre,rol,clave_hash) VALUES(?,?,?,?)",
                      (u, nom, rol, hash_clave(clave)))
    if not c.execute("SELECT 1 FROM pacientes LIMIT 1").fetchone():
        for cod, nom, edad, sexo, notas in PACIENTES_FICTICIOS:
            c.execute("INSERT INTO pacientes(codigo,nombre,edad,sexo,notas) VALUES(?,?,?,?,?)",
                      (cod, nom, edad, sexo, notas))
    con.commit()
    con.close()


def verificar_usuario(usuario, clave):
    con = conectar()
    r = con.execute("SELECT * FROM usuarios WHERE usuario=?", (usuario,)).fetchone()
    con.close()
    if r and r["clave_hash"] == hash_clave(clave):
        return dict(usuario=r["usuario"], nombre=r["nombre"], rol=r["rol"])
    return None


def pacientes():
    con = conectar()
    filas = con.execute("""SELECT p.*, (SELECT COUNT(*) FROM estudios e WHERE e.paciente_id=p.id) n_estudios
                           FROM pacientes p ORDER BY p.codigo""").fetchall()
    con.close()
    return [dict(f) for f in filas]


def paciente(pid):
    con = conectar()
    p = con.execute("SELECT * FROM pacientes WHERE id=?", (pid,)).fetchone()
    estudios = con.execute("SELECT * FROM estudios WHERE paciente_id=? ORDER BY fecha DESC", (pid,)).fetchall()
    con.close()
    return (dict(p) if p else None), [dict(e) for e in estudios]


def guardar_estudio(paciente_id, archivo_nombre, pred):
    import json
    con = conectar()
    cur = con.execute("""INSERT INTO estudios(paciente_id,fecha,archivo_nombre,clase_predicha,clase_es,confianza,
        confianza_baja,area_pct,version_modelos,imagen_b64,mascara_b64,probabilidades)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (paciente_id, datetime.now().strftime("%Y-%m-%d %H:%M"), archivo_nombre, pred["clase"], pred["clase_es"],
         pred["confianza"], int(pred["confianza_baja"]), pred["area_pct"], pred["version_modelos"],
         pred["imagen"], pred["mascara"], json.dumps(pred["probabilidades_es"], ensure_ascii=False)))
    eid = cur.lastrowid
    # registro de monitoreo (sin imagen ni datos personales)
    p = pred["probabilidades"]
    con.execute("""INSERT INTO predicciones(fecha,version_modelos,clase,prob_glioma,prob_meningioma,prob_pituitary,
        prob_no_tumor,confianza,confianza_baja,area_pct,tiempo_ms,brillo_medio) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), pred["version_modelos"], pred["clase"], p["glioma"],
         p["meningioma"], p["pituitary"], p["no_tumor"], pred["confianza"], int(pred["confianza_baja"]),
         pred["area_pct"], pred["tiempo_ms"], pred["brillo_medio"]))
    con.commit(); con.close()
    return eid


def estudio(eid):
    con = conectar()
    e = con.execute("SELECT * FROM estudios WHERE id=?", (eid,)).fetchone()
    p = con.execute("SELECT * FROM pacientes WHERE id=?", (e["paciente_id"],)).fetchone() if e else None
    con.close()
    return (dict(e) if e else None), (dict(p) if p else None)


def guardar_revision(eid, estado, clase, comentario, medico):
    con = conectar()
    con.execute("""UPDATE estudios SET revision_estado=?, revision_clase=?, revision_comentario=?,
        revision_medico=?, revision_fecha=? WHERE id=?""",
        (estado, clase, comentario, medico, datetime.now().strftime("%Y-%m-%d %H:%M"), eid))
    con.commit(); con.close()


def metricas_monitoreo():
    con = conectar()
    filas = con.execute("SELECT * FROM predicciones").fetchall()
    con.close()
    filas = [dict(f) for f in filas]
    if not filas:
        return dict(total=0)
    import statistics
    clases = {}
    for f in filas:
        clases[f["clase"]] = clases.get(f["clase"], 0) + 1
    confs = [f["confianza"] for f in filas]
    tiempos = sorted(f["tiempo_ms"] for f in filas)
    brillos = [f["brillo_medio"] for f in filas]
    p95 = tiempos[min(len(tiempos) - 1, int(0.95 * len(tiempos)))]
    return dict(
        total=len(filas), por_clase=clases,
        confianza_media=round(statistics.mean(confs) * 100, 1),
        pct_alertas=round(100 * sum(f["confianza_baja"] for f in filas) / len(filas), 1),
        tiempo_p95_ms=round(p95, 1),
        brillo_medio=round(statistics.mean(brillos), 1),
        ultimas=filas[-10:][::-1],
    )


if __name__ == "__main__":
    iniciar()
    print("Base de datos iniciada en", BD)
