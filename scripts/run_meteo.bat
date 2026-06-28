@echo off
cd /d "%~dp0.."
"C:\Program Files\Git\bin\bash.exe" scripts/run_meteo.sh > meteo_erreur.log 2>&1
