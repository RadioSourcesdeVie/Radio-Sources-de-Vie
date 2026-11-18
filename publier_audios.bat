@echo off
chcp 65001 >nul
title Radio Sources de Vie - Publier les audios sur le site
echo.
echo ================================================================
echo   Publication des audios du jour sur le site
echo ================================================================
echo.

cd /d "%~dp0"
where git >nul 2>&1
if errorlevel 1 set "PATH=%PATH%;C:\Program Files\Git\cmd"

if exist ".git\index.lock" (
  echo [ATTENTION] Un verrou git existe : une autre tache est peut-etre
  echo en train de publier. Attendez 2 minutes puis relancez ce fichier.
  echo.
  pause
  exit /b 1
)

echo Fichiers en attente de publication :
git status --short
echo.

git add -A
git commit -m "Audios du jour (publication manuelle)"
git pull --rebase --autostash origin main
git push origin main
if errorlevel 1 goto echec

echo.
echo ================================================================
echo   C'EST PUBLIE
echo ================================================================
echo.
git log -1 --stat
echo.
echo Le site se met a jour dans 1 a 2 minutes.
echo Ensuite : Ctrl + F5 sur radiosourcesdevie.org
echo.
pause
exit /b 0

:echec
echo.
echo [ERREUR] La publication a echoue. Copiez-moi tout ce texte.
echo.
pause
exit /b 1
