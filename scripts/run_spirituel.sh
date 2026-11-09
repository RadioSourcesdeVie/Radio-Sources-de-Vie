#!/bin/bash
# Radio Sources de Vie — Contenu SPIRITUEL (05h00)
#
#   Priere du SOIR  -> pour AUJOURD'HUI  (diffusee a 21h)
#   Priere du MATIN -> pour DEMAIN       (prete une journee a l'avance,
#                                         pour pouvoir la poster sur YouTube)
#
# La meteo et les news ont leurs propres taches => zero doublon.
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
source .env
TODAY=$(date '+%Y-%m-%d')
DEMAIN=$(date -d tomorrow '+%Y-%m-%d' 2>/dev/null || date -v+1d '+%Y-%m-%d')
echo "🙏 Contenu spirituel — $(date '+%Hh%M')"
echo "===== SPIRITUEL lancé le $(date) =====" >> "journal_taches.log"

# 1) Textes du jour : temoignage, sermon, priere du soir
python generate_content.py --api-key "$ANTHROPIC_KEY" --type all
python generate_sermon.py  --api-key "$ANTHROPIC_KEY"
python generate_daily.py   --api-key "$ANTHROPIC_KEY" --type soir

# 2) Texte de la priere du matin de DEMAIN
python generate_daily.py   --api-key "$ANTHROPIC_KEY" --type matin --date demain

# 3) Audio du jour (tout sauf la priere du matin, deja faite hier)
python generate_daily_audio.py

# 4) Audio de la priere du matin de demain
python generate_daily_audio.py --date demain --only "Priere Matin"

# 5) Flux RSS
python generate_rss.py

# 6) Copies vers RadioDJ — la priere du matin du JOUR a ete faite hier
cp "audio/prayers/matin_${TODAY}.mp3"  "Priere/Priere du matin/priere_matin.mp3"  2>/dev/null || true
cp "audio/prayers/soir_${TODAY}.mp3"   "Priere/Priere du soir/priere_soir.mp3"    2>/dev/null || true
cp "audio/testimonies/${TODAY}.mp3"    "Priere/Temoignage/temoignage.mp3"         2>/dev/null || true
cp "audio/sermons/${TODAY}.mp3"        "Sermon/sermon.mp3"                        2>/dev/null || true

# 7) Publication
git pull origin main --no-edit
git add -A
git commit -m "Contenu spirituel $(date '+%Y-%m-%d %Hh%M')"
git push origin main

echo
echo "✅ Spirituel OK"
echo "📺 Prete a poster sur YouTube : audio/prayers/matin_${DEMAIN}.mp3"
