@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Radio Sources de Vie - Generation des prieres YouTube ===
echo.
py -m pip install --quiet edge-tts pydub
py priere_youtube.py
echo.
pause
