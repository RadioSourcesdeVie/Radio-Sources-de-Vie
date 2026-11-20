@echo off
cd /d "%~dp0"
echo === Publication de la page Psaumes sur GitHub ===
git add psaumes.html index.html
git add psaumes/Psaume_*.mp3
git commit -m "Ajout page Psaumes et 150 audios"
git push
echo.
echo Termine. Verifie l'onglet Actions sur GitHub (1 a 3 minutes).
pause
