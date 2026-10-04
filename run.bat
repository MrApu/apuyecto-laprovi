@echo off
cd /d "%~dp0"
set PYTHON_EXE=.python\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)
"%PYTHON_EXE%" main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================================
    echo Ocurrio un error al ejecutar la aplicacion.
    echo ========================================================
    pause
)
