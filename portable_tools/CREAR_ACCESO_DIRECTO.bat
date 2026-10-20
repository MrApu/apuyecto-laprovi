@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   CREANDO ACCESO DIRECTO EN EL ESCRITORIO
echo ========================================================
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ws = New-Object -ComObject WScript.Shell; $desktop = [System.Environment]::GetFolderPath('Desktop'); $s = $ws.CreateShortcut([System.IO.Path]::Combine($desktop, 'La Provincial.lnk')); $s.TargetPath = [System.IO.Path]::Combine((Get-Location).Path, 'LaProvincial.exe'); $s.WorkingDirectory = (Get-Location).Path; $s.Description = 'Sistema de Control La Provincial'; $s.Save()"
echo.
echo [EXITO] Acceso directo 'La Provincial' creado en tu Escritorio.
echo Ya puedes abrir el sistema directamente desde tu pantalla de inicio.
echo ========================================================
pause
