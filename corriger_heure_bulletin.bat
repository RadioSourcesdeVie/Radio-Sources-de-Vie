@echo off
chcp 65001 >nul
title Radio Sources de Vie - Heure du Journal du Soir
echo.
echo ================================================================
echo   Journal du Soir : generation avancee a 17h45
echo ================================================================
echo.
echo   Avant : la tache demarrait a 18h00 pile, pendant que
echo           RadioDJ diffusait deja. Le journal mis a l'antenne
echo           etait donc celui de la veille.
echo.
echo   La generation prend 3 minutes 25 secondes.
echo   A 17h45, le fichier est pret a 17h49 : quinze minutes
echo   de marge avant la diffusion.
echo.

schtasks /Change /TN "RSDV_BulletinSoir_18" /ST 17:45

if errorlevel 1 goto echec

echo.
echo ================================================================
echo   HEURE MODIFIEE
echo ================================================================
echo.
schtasks /Query /TN "RSDV_BulletinSoir_18" /FO LIST
echo.
pause
exit /b 0

:echec
echo.
echo [ERREUR] L'heure n'a pas pu etre modifiee.
echo.
echo Fermez cette fenetre, faites un CLIC DROIT sur ce fichier
echo et choisissez "Executer en tant qu'administrateur".
echo.
echo Si le nom de la tache a change, listez-les avec :
echo    schtasks /Query /FO TABLE
echo.
pause
exit /b 1
