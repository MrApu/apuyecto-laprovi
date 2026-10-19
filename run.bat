@echo off
chcp 65001 > nul
cd /d "%~dp0"

if exist ".python\python.exe" (
    ".python\python.exe" main.py
    goto :check_err
)

if exist "dist\LaProvincial\LaProvincial.exe" (
    start "" "dist\LaProvincial\LaProvincial.exe"
    exit /b 0
)

if exist "LaProvincial.exe" (
    start "" "LaProvincial.exe"
    exit /b 0
)

python main.py

:check_err
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================================
    echo Ocurrio un error al ejecutar la aplicacion.
    echo ========================================================
    pause
)
