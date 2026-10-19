@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ==========================================================
echo   GENERANDO EJECUTABLE DE LA PROVINCIAL (.EXE)
echo ==========================================================

set PYTHON_EXE=.python\python.exe

if not exist "%PYTHON_EXE%" (
    echo [INFO] Usando python del sistema...
    set PYTHON_EXE=python
)

echo [1/3] Ejecutando PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --windowed --name "LaProvincial" --add-data "database\schema.sql;database" --add-data "resources;resources" main.py

echo [2/3] Copiando base de datos actual al paquete distribuible...
if exist "control_policial.db" (
    copy /Y "control_policial.db" "dist\LaProvincial\control_policial.db" > nul
    echo [OK] Base de datos control_policial.db sincronizada en dist\LaProvincial\
)

echo [3/3] Verificando ejecutable...
if exist "dist\LaProvincial\LaProvincial.exe" (
    echo ==========================================================
    echo   EJECUTABLE GENERADO EXITOSAMENTE:
    echo   dist\LaProvincial\LaProvincial.exe
    echo ==========================================================
) else (
    echo [ERROR] No se pudo generar el ejecutable.
)
pause
