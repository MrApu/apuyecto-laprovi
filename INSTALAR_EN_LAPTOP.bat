@echo off
chcp 65001 > nul
title INSTALADOR - LA PROVINCIAL (Control Policial y Finanzas)
cd /d "%~dp0"

echo ======================================================================
echo        INSTALADOR DE LA PROVINCIAL - RESTAURANTE ^& FAST FOOD
echo        Sistema de Gestion Comercial y Control Policial PNP
echo ======================================================================
echo.

REM Detectar origen del ejecutable (ya sea desde la raiz del proyecto o dentro de dist\LaProvincial)
set "SRC_EXE="
set "SRC_DIR="

if exist "%~dp0LaProvincial.exe" (
    set "SRC_DIR=%~dp0"
    set "SRC_EXE=%~dp0LaProvincial.exe"
) else if exist "%~dp0dist\LaProvincial\LaProvincial.exe" (
    set "SRC_DIR=%~dp0dist\LaProvincial"
    set "SRC_EXE=%~dp0dist\LaProvincial\LaProvincial.exe"
)

if "%SRC_EXE%"=="" (
    echo [AVISO] No se encontro LaProvincial.exe compilado.
    if exist "%~dp0run.bat" (
        echo Se configurara el acceso directo usando run.bat en esta carpeta.
        set "TARGET_DIR=%~dp0"
        set "TARGET_LAUNCH=%~dp0run.bat"
        goto :create_shortcut
    ) else (
        echo [ERROR] No se encontraron los archivos del programa.
        pause
        exit /b 1
    )
)

echo Seleccione como desea instalar el programa en esta Laptop:
echo.
echo   [1] INSTALACION COMPLETA EN DISCO LOCAL (C:\LaProvincial) - RECOMENDADO
echo       (Copia el programa desde el USB a C:\LaProvincial y crea el icono en el Escritorio)
echo.
echo   [2] USAR EN ESTA MISMA CARPETA (Solo crear icono en el Escritorio)
echo       (Ideal si ya copiaste la carpeta del USB al disco de la laptop)
echo.
set /p OPCION="Ingrese 1 o 2 (Presione ENTER para elegir 1): "
if "%OPCION%"=="" set "OPCION=1"

if "%OPCION%"=="2" (
    set "TARGET_DIR=%SRC_DIR%"
    set "TARGET_LAUNCH=%SRC_EXE%"
    if exist "%~dp0control_policial.db" (
        if not exist "%SRC_DIR%\control_policial.db" (
            copy /Y "%~dp0control_policial.db" "%SRC_DIR%\control_policial.db" > nul
        )
    )
    goto :create_shortcut
)

set "TARGET_DIR=C:\LaProvincial"
echo.
echo [1/3] Copiando archivos del programa a %TARGET_DIR% ...
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
if %ERRORLEVEL% NEQ 0 (
    set "TARGET_DIR=%USERPROFILE%\LaProvincial"
    echo [INFO] Usando carpeta de usuario: %TARGET_DIR%
    if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"
)

xcopy "%SRC_DIR%\*" "%TARGET_DIR%\" /E /I /Y /Q > nul

REM Si existe control_policial.db en la raiz del USB/proyecto, asegurar que se copie la mas reciente
if exist "%~dp0control_policial.db" (
    copy /Y "%~dp0control_policial.db" "%TARGET_DIR%\control_policial.db" > nul
)

if not exist "%TARGET_DIR%\backups_db" mkdir "%TARGET_DIR%\backups_db"

set "TARGET_LAUNCH=%TARGET_DIR%\LaProvincial.exe"
echo [OK] Archivos copiados correctamente en: %TARGET_DIR%

:create_shortcut
echo.
echo [2/3] Creando acceso directo "LA PROVINCIAL" en el Escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$desktop = [Environment]::GetFolderPath('Desktop'); ^
     $lnkPath = Join-Path $desktop 'LA PROVINCIAL.lnk'; ^
     $wsh = New-Object -ComObject WScript.Shell; ^
     $sc = $wsh.CreateShortcut($lnkPath); ^
     $sc.TargetPath = '%TARGET_LAUNCH%'; ^
     $sc.WorkingDirectory = '%TARGET_DIR%'; ^
     $sc.Description = 'LA PROVINCIAL - Sistema de Gestion Comercial y Control Policial PNP'; ^
     $sc.Save(); ^
     Write-Host '[OK] Acceso directo creado en:' $lnkPath"

echo.
echo [3/3] Verificando base de datos...
if exist "%TARGET_DIR%\control_policial.db" (
    echo [OK] Base de datos activa: %TARGET_DIR%\control_policial.db
) else (
    echo [INFO] La base de datos se inicializara automaticamente al abrir el programa.
)

echo.
echo ======================================================================
echo   INSTALACION COMPLETADA CON EXITO
echo   Ya puedes retirar tu USB (si elegiste la opcion 1) y abrir el
echo   programa desde el icono "LA PROVINCIAL" en tu Escritorio.
echo ======================================================================
echo.
set /p ABRIR="¿Desea abrir LA PROVINCIAL ahora mismo? (S/N, Enter=S): "
if /I not "%ABRIR%"=="N" (
    start "" "%TARGET_LAUNCH%"
)
pause
