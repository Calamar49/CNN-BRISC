@echo off
REM Inicia la aplicacion de demostracion NeuroBRISC (Windows). Requiere el entorno .venv del proyecto
REM y los modelos ONNX en modelos\ (generados con exportar_onnx.py). No necesita internet ni GPU.
setlocal
cd /d "%~dp0"
set VENV=..\..\.venv\Scripts\python.exe
if not exist "%VENV%" (
  echo No encuentro el entorno en %VENV%. Crea el .venv e instala requirements-app.txt.
  pause
  exit /b 1
)
echo Iniciando NeuroBRISC en http://localhost:8000  (Ctrl+C para detener)
start "" http://localhost:8000
"%VENV%" -m uvicorn app.servidor:app --port 8000 --host 127.0.0.1
endlocal
