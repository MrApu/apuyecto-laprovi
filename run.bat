@echo off
set PYTHON_EXE=.python\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=python
)
"%PYTHON_EXE%" main.py
