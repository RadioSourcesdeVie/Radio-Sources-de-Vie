@echo off
cd /d "%~dp0.."
echo Publication du lien Musique dans le menu...
git add index.html
git commit -m "Ajout du lien Musique dans le menu"
git push origin main
if errorlevel 1 (
    echo Push vers 'main' a echoue, essai avec 'master'...
    git push origin master
)
echo.
echo Termine !
pause
