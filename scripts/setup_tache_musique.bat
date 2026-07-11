@echo off
schtasks /create /tn "RSDV_Liste_Musique" /tr "C:\Users\avena\Desktop\Radio Sources De Vie\scripts\generer_liste_auto.bat" /sc daily /st 04:00 /f
echo.
echo Tache planifiee creee : RSDV_Liste_Musique (tous les jours a 04:00)
echo La page musique.html sera regeneree automatiquement chaque nuit.
pause
