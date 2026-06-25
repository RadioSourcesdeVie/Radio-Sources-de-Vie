@echo off
cd /d "%~dp0.."
echo DOSSIER ACTUEL: %CD% > task_debug.log
echo --- >> task_debug.log
"C:\Program Files\Git\bin\bash.exe" scripts/run_news.sh >> task_debug.log 2>&1
echo FIN CODE: %ERRORLEVEL% >> task_debug.log
