@echo off
rem Lanceur appele par la tache planifiee de 13h.
rem Se place dans le dossier de la radio puis execute le script bash.
cd /d "%~dp0"

set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%BASH%" set "BASH=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
if not exist "%BASH%" set "BASH=%ProgramFiles(x86)%\Git\bin\bash.exe"
if not exist "%BASH%" set "BASH=C:\Git\bin\bash.exe"

if not exist "%BASH%" (
  echo [%date% %time%] ERREUR : bash.exe introuvable >> journal_taches.log
  exit /b 1
)

"%BASH%" scripts/run_priere_matin.sh >> journal_taches.log 2>&1
