@echo off
cd /d "%~dp0"
git add psaumes.html
git add PsaumesMusique/
git commit -m "Psaumes: version avec musique + choix voix seule"
git push
pause
