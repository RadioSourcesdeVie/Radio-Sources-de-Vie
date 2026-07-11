@echo off
cd /d "%~dp0.."
echo Publication de musique.html sur GitHub...
git add musique.html
git commit -m "Ajout / mise a jour de la bibliotheque musicale"
git push origin main
if errorlevel 1 (
    echo Push vers 'main' a echoue, essai avec 'master'...
    git push origin master
)
echo.
echo Termine ! Le site va se mettre a jour dans quelques minutes.
pause
