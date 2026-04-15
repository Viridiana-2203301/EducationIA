@echo off
SET VENV_NAME=EducationIA

:: 1. Verificar si la carpeta del entorno ya existe
if not exist %VENV_NAME% (
    echo [SISTEMA] Creando entorno virtual...
    python -m venv %VENV_NAME%
) else (
    echo [SISTEMA] El entorno virtual ya existe.
)

:: 2. Activar el entorno
echo [SISTEMA] Activando...
call %VENV_NAME%\Scripts\activate

:: 3. Actualizar pip e instalar requerimientos
echo [SISTEMA] Actualizando pip...
python -m pip install --upgrade pip

if exist requirements.txt (
    echo [SISTEMA] Instalando librerias...
    pip install -r requirements.txt
) else (
    echo [AVISO] No se encontro requirements.txt.
)

echo [LISTO] Entorno configurado y activo.
cmd /k