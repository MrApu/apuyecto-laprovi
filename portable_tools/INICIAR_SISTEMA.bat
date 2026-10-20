@echo off
chcp 65001 > nul
cd /d "%~dp0"
title Sistema La Provincial
echo ===================================================
echo   INICIANDO SISTEMA DE CONTROL POLICIAL
echo   LA PROVINCIAL
echo ===================================================
start "" "LaProvincial.exe"
exit
