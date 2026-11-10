@echo off
chcp 65001 >nul
title Radio Sources de Vie - Tache de 13h
echo.
echo ================================================================
echo   Radio Sources de Vie
echo   Priere du matin du lendemain, chaque jour a 13h00
echo ================================================================
echo.

set "DOSSIER=%~dp0"
if "%DOSSIER:~-1%"=="\" set "DOSSIER=%DOSSIER:~0,-1%"
set "LANCEUR=%DOSSIER%\lancer_priere_matin.bat"

if not exist "%LANCEUR%" (
  echo [ERREUR] Fichier introuvable :
  echo    %LANCEUR%
  echo.
  echo Ce fichier doit se trouver dans le meme dossier que cet installateur.
  echo.
  pause
  exit /b 1
)

echo Lanceur : %LANCEUR%
echo.

rem --- Supprimer d'abord toute ancienne version de la tache ---
schtasks /Delete /TN "RSDV Priere du matin 13h" /F >nul 2>&1

rem --- Creer la tache. Le lanceur ecrit tout dans journal_taches.log,
rem     donc en cas de probleme on verra l'erreur au lieu de rien.
schtasks /Create ^
 /TN "RSDV Priere du matin 13h" ^
 /TR "\"%LANCEUR%\"" ^
 /SC DAILY ^
 /ST 13:00 ^
 /F

if errorlevel 1 goto echec

echo.
echo ================================================================
echo   TACHE CREEE
echo ================================================================
echo.
echo Verification :
echo.
schtasks /Query /TN "RSDV Priere du matin 13h" /FO LIST
echo.
echo ----------------------------------------------------------------
echo Pour la tester tout de suite, sans attendre 13h :
echo    schtasks /Run /TN "RSDV Priere du matin 13h"
echo.
echo Le resultat s'ecrira dans journal_taches.log
echo ----------------------------------------------------------------
echo.
pause
exit /b 0

:echec
echo.
echo [ERREUR] La tache n'a pas pu etre creee.
echo.
echo Fermez cette fenetre, faites un CLIC DROIT sur
echo    installer_tache_13h.bat
echo et choisissez "Executer en tant qu'administrateur".
echo.
pause
exit /b 1
