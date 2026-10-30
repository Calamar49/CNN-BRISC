# NeuroBRISC — aplicación de demostración (HU13)

Prototipo de **sistema clínico** con el flujo principal de **apoyo al diagnóstico en neuro-oncología**: se sube una
resonancia T1 con contraste, el sistema sugiere el tipo de tumor y marca su contorno, y el médico revisa. Los demás
módulos son maqueta. **No es una herramienta de diagnóstico médico.** Pacientes y usuarios ficticios; todo se
procesa en local.

## Cómo ejecutarla

Requiere los modelos ONNX desplegados (`../modelos/clasificador_v1.onnx` y `segmentacion_v1.onnx`): se generan con
`python ../exportar_onnx.py` (ver el README del Sprint 3).

```bash
# desde "03. Implementacion/Sprint 3 - Evaluacion y despliegue"
pip install -r requirements-app.txt
python -m uvicorn app.servidor:app --port 8000
# abrir http://localhost:8000
```

En Windows se puede usar el script `iniciar_demo.bat` (activa el entorno y abre el navegador).

**Acceso de demostración:** médico `medico / medico123` · administrador `admin / admin123` (usuarios ficticios,
claves guardadas con hash). Trae 5 imágenes de ejemplo de **validación** (no de prueba).

## Funciona sin internet

No se cargan fuentes, CSS ni JavaScript de ningún CDN (se usan las fuentes del sistema). La inferencia corre con
ONNX Runtime en **CPU**, sin GPU. No se envía ninguna imagen a servicios externos.

## El flujo principal (pantallas 1–8)

1. **Ingreso** como médico (o administrador).
2. **Casos** — lista de pacientes ficticios.
3. **Caso** — datos del paciente y botón «Nuevo estudio de neuro-oncología».
4. **Subir** la resonancia T1 (o elegir un ejemplo), con validación de la entrada.
5. **Procesando** en el servidor local (segundos).
6. **Resultado** — imagen con el contorno del tumor y control de opacidad, clase sugerida con las 4
   probabilidades, área del tumor y alerta de confianza baja (< 80 %).
7. **Revisión del médico** — acepta o corrige la clase y escribe un comentario.
8. **Informe del caso** — vista imprimible (PDF) con la versión de los modelos y el aviso de demostración.

Además: **ficha de los modelos** (métricas de validación y de la prueba oficial, uso previsto y limitaciones),
**monitoreo** (registro de predicciones sin imágenes ni datos personales: distribución de clases, confianza media,
porcentaje de alertas, tiempo p95 y brillo medio como señal de deriva) y **módulos maqueta**.

## Reglas de decisión (plan, sección 6.3)

- Si el clasificador predice «sin tumor», **no se muestra contorno** (el segmentador solo se entrenó con imágenes
  con tumor).
- Si la probabilidad más alta es **< 80 %**, se marca «confianza baja: requiere revisión del médico» (umbral
  propuesto, no medido).
- Se valida la entrada: formato PNG/JPG y brillo medio del cerebro dentro del rango de entrenamiento (~36–161);
  si no, se advierte.

## Estructura

```
servidor.py     FastAPI: rutas del flujo, módulos maqueta, ficha del modelo, monitoreo
inferencia.py   carga los ONNX, preprocesa y aplica las reglas de decisión
basedatos.py    SQLite: usuarios y pacientes ficticios, estudios, registro de predicciones (monitoreo)
plantillas/     Jinja2 (base, login, casos, caso, estudio, resultado, informe, ficha_modelo, admin, maqueta, acerca)
estatico/       estilos.css (blanco/formal, sin CDN) y app.js
datos_demo/     demo.sqlite y 5 imágenes de ejemplo de validación (ignorado por Git)
```
