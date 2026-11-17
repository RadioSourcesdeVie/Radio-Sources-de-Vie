@echo off
rem Test : genere le Psaume 1 avec ta voix (Gemini 3.8 Flash TTS)
cd /d "%~dp0.."
where py >nul 2>nul && (py Psaumes\generer_psaumes.py 1) || (python Psaumes\generer_psaumes.py 1)
echo.
echo Ecoute le resultat : Psaumes\audio\Psaume_001.mp3
pause
