#!/bin/bash
# Radio Sources de Vie — Prieres du LENDEMAIN, preparees le soir.
# Objectif : avoir les deux prieres pretes a poster sur YouTube avant la nuit.
# A 05h, run_spirituel.sh les trouvera deja faites et ne les refera pas.
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
source .env

DEMAIN=$(date -d tomorrow '+%Y-%m-%d' 2>/dev/null || date -v+1d '+%Y-%m-%d')
echo "🌙 Prieres du $DEMAIN — preparees le $(date '+%d/%m a %Hh%M')"
echo "===== PRIERES DEMAIN lancees le $(date) =====" >> "journal_taches.log"

# 1) Textes : les deux prieres de 10 minutes
python generate_daily.py --api-key "$ANTHROPIC_KEY" --date demain || exit 1

# 2) Audio : UNIQUEMENT les deux prieres.
#    Sans --only, la meteo de demain serait fabriquee avec les
#    temperatures d'aujourd'hui, et la tache de 5h la sauterait.
python generate_daily_audio.py --date demain --only "Priere Matin,Priere Soir"

# 3) Publication
git pull origin main --no-edit
git add -A
git commit -m "Prieres du $DEMAIN preparees la veille"
git push origin main

echo
echo "✅ Pretes a poster sur YouTube :"
for m in matin soir; do
  f="audio/prayers/${m}_${DEMAIN}.mp3"
  [ -f "$f" ] && echo "   $(pwd)/$f  ($(( $(stat -c%s "$f") / 1024 )) Ko)"
done
