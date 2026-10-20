@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ==========================================================
echo   GENERANDO EJECUTABLE Y PAQUETE PORTABLE LA PROVINCIAL
echo ==========================================================

set PYTHON_EXE=.python\python.exe

if not exist "%PYTHON_EXE%" (
    echo [INFO] Usando python del sistema...
    set PYTHON_EXE=python
)

echo [1/4] Ejecutando PyInstaller...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --onedir --windowed --name "LaProvincial" --add-data "database\schema.sql;database" --add-data "resources;resources" main.py

echo [2/4] Copiando base de datos actual al paquete distribuible...
if exist "control_policial.db" (
    copy /Y "control_policial.db" "dist\LaProvincial\control_policial.db" > nul
    echo [OK] Base de datos control_policial.db sincronizada en dist\LaProvincial\
)

echo [3/4] Agregando herramientas portables y lanzadores...
if exist "portable_tools" (
    copy /Y "portable_tools\*" "dist\LaProvincial\" > nul
    echo [OK] Herramientas portables y lanzadores copiados a dist\LaProvincial\
)

echo [4/4] Verificando ejecutable...
if exist "dist\LaProvincial\LaProvincial.exe" (
    echo ==========================================================
    echo   PAQUETE PORTABLE GENERADO EXITOSAMENTE:
    echo   Carpeta:  dist\LaProvincial\
    echo   Archivo:  dist\LaProvincial\LaProvincial.exe
    echo   Lanzador: dist\LaProvincial\INICIAR_SISTEMA.bat
    echo ==========================================================
) else (
    echo [ERROR] No se pudo generar el ejecutable.
)
pause
