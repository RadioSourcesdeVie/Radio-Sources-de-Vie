#!/bin/bash
# Radio Sources de Vie — Génération du contenu SPIRITUEL uniquement
# Prières matin/soir, Témoignages, Sermons (+ Sabbat/Bulletins).
# NE refait PAS la météo ni les news (gérées par leurs propres tâches) => zéro doublon.
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
source .env
TODAY=$(date '+%Y-%m-%d')
echo "🙏 Contenu spirituel — $(date '+%Hh%M')"
echo "===== SPIRITUEL lancé le $(date) =====" >> "journal_taches.log"

# 1) Textes (Claude Haiku) : prières, témoignages, sermons, sabbat, bulletins
python generate_content.py --api-key "$ANTHROPIC_KEY" --type all
python generate_sermon.py  --api-key "$ANTHROPIC_KEY"
python generate_daily.py   --api-key "$ANTHROPIC_KEY"

# 2) Audio (Edge TTS, gratuit — voix Sylvie/Denise/Henri)
python generate_daily_audio.py

# 3) Flux RSS + publication
python generate_rss.py

# 4) Copies vers RadioDJ (mêmes chemins que run_meteo.sh)
cp "audio/prayers/matin_${TODAY}.mp3"  "Priere/Priere du matin/priere_matin.mp3"  2>/dev/null || true
cp "audio/prayers/soir_${TODAY}.mp3"   "Priere/Priere du soir/priere_soir.mp3"    2>/dev/null || true
cp "audio/testimonies/${TODAY}.mp3"    "Priere/Temoignage/temoignage.mp3"         2>/dev/null || true

# 5) Publication sur le site (GitHub Pages)
git pull origin main --no-edit
git add -A
git commit -m "Contenu spirituel $(date '+%Y-%m-%d %Hh%M')"
git push origin main
echo "✅ Spirituel OK"
