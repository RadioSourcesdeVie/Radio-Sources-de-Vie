@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Generation des prieres - RSDV

where py >nul 2>nul
if errorlevel 1 (
    echo ERREUR : Python n'est pas installe ^(commande "py" introuvable^).
    pause
    exit /b
)

echo Verification de edge-tts...
py -m pip install --quiet --upgrade edge-tts

py priere_youtube.py

echo.
pause