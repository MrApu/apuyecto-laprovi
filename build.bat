@echo off
chcp 65001 > nul
echo ==========================================================
echo   GENERANDO EJECUTABLE DE CONTROL POLICIAL (.EXE)
echo ==========================================================

set PYTHON_EXE=.python\python.exe

if not exist "%PYTHON_EXE%" (
    echo [INFO] Usando python del sistema...
    set PYTHON_EXE=python
)

echo [1/3] Verificando dependencias...
"%PYTHON_EXE%" -m pip install -r requirements.txt

echo [2/3] Ejecutando PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --windowed --name "LaProvincial" --add-data "database\schema.sql;database" --add-data "resources;resources" main.py

echo [3/3] Creando acceso directo y verificando...
if exist "dist\LaProvincial\LaProvincial.exe" (
    echo ==========================================================
    echo   EJECUTABLE GENERADO EXITOSAMENTE:
    echo   dist\LaProvincial\LaProvincial.exe
    echo ==========================================================
) else (
    echo [ERROR] No se pudo generar el ejecutable.
)
pause
