#!/bin/bash
# Radio Sources de Vie — PRIERE DU MATIN du lendemain (13h00)
#
# Pourquoi 13h et pas 5h du matin :
#   - RadioDJ diffuse la priere a 5h. La fabriquer a 4h ne laissait
#     qu'une cinquantaine de minutes de marge. Ici on a quinze heures.
#   - Le fichier est pret des l'apres-midi pour etre poste sur YouTube.
#
# Ce script copie directement le MP3 dans le dossier RadioDJ.
# sync_radiodj.sh ne touche plus a la priere du matin, sinon il
# remettrait celle d'aujourd'hui a la place de celle de demain.
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
source .env

DEMAIN=$(date -d tomorrow '+%Y-%m-%d' 2>/dev/null || date -v+1d '+%Y-%m-%d')
echo "🌅 Priere du matin du $DEMAIN — preparee le $(date '+%d/%m a %Hh%M')"
echo "===== PRIERE MATIN lancee le $(date) =====" >> "journal_taches.log"

# 1) Texte
python generate_daily.py --api-key "$ANTHROPIC_KEY" --type matin --date demain || exit 1

# 2) Audio (voix clonee, style calme)
python generate_daily_audio.py --date demain --only "Priere Matin" || exit 1

# 3) Mise en place pour RadioDJ, quinze heures avant la diffusion
MP3="audio/prayers/matin_${DEMAIN}.mp3"
if [ -f "$MP3" ]; then
  cp "$MP3" "Priere/Priere du matin/priere_matin.mp3"
  echo "📻 Copie vers RadioDJ : $(( $(stat -c%s "$MP3") / 1024 )) Ko"
else
  echo "⚠️  $MP3 introuvable — RadioDJ garde le fichier precedent"
fi

# 4) Publication
git pull origin main --no-edit
git add -A
git commit -m "Priere du matin du $DEMAIN"
git push origin main

echo
echo "✅ Prete a poster sur YouTube :"
echo "   $(pwd)/$MP3"
