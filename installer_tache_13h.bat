@echo off
chcp 65001 >nul
title Radio Sources de Vie - Installation de la tache de 13h
echo.
echo ================================================================
echo   Radio Sources de Vie
echo   Tache quotidienne : Priere du matin du lendemain, a 13h00
echo ================================================================
echo.

set "DOSSIER=%~dp0"
if "%DOSSIER:~-1%"=="\" set "DOSSIER=%DOSSIER:~0,-1%"

rem --- Trouver bash.exe (Git pour Windows) ---
set "BASH="
for %%P in (
  "%ProgramFiles%\Git\bin\bash.exe"
  "%ProgramFiles(x86)%\Git\bin\bash.exe"
  "%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
  "%USERPROFILE%\AppData\Local\Programs\Git\bin\bash.exe"
  "C:\Git\bin\bash.exe"
) do if not defined BASH if exist %%P set "BASH=%%~P"

if not defined BASH (
  echo [ERREUR] bash.exe introuvable.
  echo Git pour Windows ne semble pas installe a un emplacement connu.
  echo Envoyez ce message a Claude, il adaptera le script.
  echo.
  pause
  exit /b 1
)

echo Git trouve      : %BASH%
echo Dossier radio   : %DOSSIER%
echo.

schtasks /Create ^
 /TN "RSDV Priere du matin 13h" ^
 /TR "\"%BASH%\" -lc \"cd '%DOSSIER%' && bash scripts/run_priere_matin.sh\"" ^
 /SC DAILY ^
 /ST 13:00 ^
 /F

if errorlevel 1 (
  echo.
  echo [ERREUR] La tache n'a pas pu etre creee.
  echo Faites un clic droit sur ce fichier et choisissez
  echo "Executer en tant qu'administrateur".
) else (
  echo.
  echo ================================================================
  echo   TACHE CREEE : "RSDV Priere du matin 13h"
  echo   Elle tournera chaque jour a 13h00, a partir d'aujourd'hui.
  echo ================================================================
  echo.
  echo Pour la verifier plus tard : Planificateur de taches Windows.
  echo Pour la lancer tout de suite :
  echo    schtasks /Run /TN "RSDV Priere du matin 13h"
)
echo.
pause
