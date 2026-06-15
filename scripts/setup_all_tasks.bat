@echo off
schtasks /create /tn "RSDV_News_11" /tr "C:\Users\avena\Desktop\Radio Sources De Vie\scripts\run_news.bat" /sc daily /st 11:00 /f
schtasks /create /tn "RSDV_News_17" /tr "C:\Users\avena\Desktop\Radio Sources De Vie\scripts\run_news.bat" /sc daily /st 17:00 /f
schtasks /create /tn "RSDV_Meteo_05" /tr "C:\Users\avena\Desktop\Radio Sources De Vie\scripts\run_meteo.bat" /sc daily /st 05:00 /f
schtasks /create /tn "RSDV_Meteo_10" /tr "C:\Users\avena\Desktop\Radio Sources De Vie\scripts\run_meteo.bat" /sc daily /st 10:00 /f
schtasks /create /tn "RSDV_Meteo_14" /tr "C:\Users\avena\Desktop\Radio Sources De Vie\scripts\run_meteo.bat" /sc daily /st 14:00 /f
schtasks /create /tn "RSDV_Meteo_17" /tr "C:\Users\avena\Desktop\Radio Sources De Vie\scripts\run_meteo.bat" /sc daily /st 17:00 /f
echo.
echo Toutes les taches sont creees!
pause