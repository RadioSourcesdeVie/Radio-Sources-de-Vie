@echo off
chcp 65001 >nul
title Radio Sources de Vie - Heure du Journal du Soir
echo.
echo ================================================================
echo   Journal du Soir : generation avancee a 17h45
echo ================================================================
echo.
echo   Avant : la tache demarrait a 18h00 pile, pendant que RadioDJ
echo           diffusait deja. L'antenne passait donc le journal
echo           de la veille.
echo.
echo   La generation prend 3 minutes 25 secondes. A 17h45 le
echo   fichier est pret a 17h49, soit onze minutes avant.
echo.
echo ----------------------------------------------------------------
echo.

set "DOSSIER=%~dp0"
if "%DOSSIER:~-1%"=="\" set "DOSSIER=%DOSSIER:~0,-1%"
set "LANCEUR=%DOSSIER%\scripts\run_bulletin_soir.bat"

if not exist "%LANCEUR%" (
  echo [ERREUR] Fichier introuvable :
  echo    %LANCEUR%
  echo.
  echo Cet installateur doit rester dans le dossier de la radio.
  echo.
  pause
  exit /b 1
)

rem --- On va DIRECTEMENT a la recreation de la tache.
rem     "schtasks /Change" redemande le mot de passe enregistre et le
rem     refuse quand on ouvre Windows avec un code PIN. Sans /RU ni /RP,
rem     "schtasks /Create" n'enregistre aucun mot de passe et ne demande
rem     rien : la tache tourne sous la session ouverte. Le PC reste
rem     allume pour RadioDJ, donc la session est ouverte a 17h45.
echo Mise en place de la tache a 17h45...
echo.

schtasks /Delete /TN "RSDV_BulletinSoir_18" /F >nul 2>&1
schtasks /Create ^
 /TN "RSDV_BulletinSoir_18" ^
 /TR "\"%LANCEUR%\"" ^
 /SC DAILY ^
 /ST 17:45 ^
 /F
if errorlevel 1 goto echec

:reussi
echo.
echo ================================================================
echo   C'EST FAIT
echo ================================================================
echo.
schtasks /Query /TN "RSDV_BulletinSoir_18" /FO LIST
echo.
echo Le journal de ce soir sera genere a 17h45.
echo.
pause
exit /b 0

:echec
echo.
echo [ERREUR] La tache n'a pas pu etre modifiee.
echo.
echo Essayez par le Planificateur de taches :
echo   1. Touche Windows, tapez : Planificateur de taches
echo   2. Bibliotheque du Planificateur de taches
echo   3. Double-clic sur RSDV_BulletinSoir_18
echo   4. Onglet Declencheurs, Modifier, 18:00 devient 17:45, OK
echo.
pause
exit /b 1
