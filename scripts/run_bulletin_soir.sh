#!/bin/bash
# Radio Sources de Vie — Journal du Soir (10-15 min, Lundi-Vendredi 18h)
# Réutilise les nouvelles déjà collectées dans la journée (content/news/*_${TODAY}.json)
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
source .env
TODAY=$(date '+%Y-%m-%d')
echo "🌆 Journal du Soir — $(date '+%Hh%M')"
echo "===== BULLETIN_SOIR lancé le $(date) =====" >> "journal_taches.log"

python generate_bulletin_soir.py --api-key "$ANTHROPIC_KEY"
python generate_rss.py --type news

mkdir -p "Nouvelles/Radio SDV Bulletin Soir"
cp "audio/bulletin_soir/${TODAY}.mp3" "Nouvelles/Radio SDV Bulletin Soir/bulletin_soir.mp3" 2>/dev/null || true

git pull origin main --no-edit
git add -A
git commit -m "Journal du soir $(date '+%Y-%m-%d %Hh%M')"
git push origin main
echo "✅ Journal du Soir OK"
