@echo off
cd /d "%~dp0"
py generer_liste_musique.py >> "%~dp0generer_liste.log" 2>&1
cd /d "%~dp0.."
git add musique.html >> "%~dp0generer_liste.log" 2>&1
git commit -m "Mise a jour auto - bibliotheque musicale" >> "%~dp0generer_liste.log" 2>&1
git push origin main >> "%~dp0generer_liste.log" 2>&1
