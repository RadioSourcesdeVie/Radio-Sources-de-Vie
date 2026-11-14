#!/bin/bash
# Radio Sources de Vie — Contenu SPIRITUEL (05h00)
#
#   Priere du SOIR  -> pour AUJOURD'HUI (diffusee a 21h)
#   La priere du MATIN est fabriquee la veille a 13h
#   par scripts/run_priere_matin.sh — pas ici.
#
# La meteo et les news ont leurs propres taches => zero doublon.
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
source .env
TODAY=$(date '+%Y-%m-%d')
echo "🙏 Contenu spirituel — $(date '+%Hh%M')"
echo "===== SPIRITUEL lancé le $(date) =====" >> "journal_taches.log"

# 1) Textes du jour : temoignage, sermon, priere du soir
# --type testimony et PAS --type all : "all" declenche aussi
# l'ancienne priere courte, qui ecrasait celle de 10 minutes.
python generate_content.py --api-key "$ANTHROPIC_KEY" --type testimony
python generate_sermon.py  --api-key "$ANTHROPIC_KEY"
python generate_daily.py   --api-key "$ANTHROPIC_KEY" --type soir

# 2) Audio du jour (la priere du matin a ete faite hier a 13h)
python generate_daily_audio.py

# 3) Flux RSS
python generate_rss.py

# 4) Copies vers RadioDJ (filet de securite : deja copie hier a 13h) — la priere du matin du JOUR a ete faite hier
# La priere du matin n'est PAS copiee ici. Elle est mise en place
# la veille a 13h par run_priere_matin.sh, qui est le SEUL script
# autorise a ecrire Priere/Priere du matin/priere_matin.mp3.
# La copier ici remettait celle d'aujourd'hui par-dessus celle de
# demain, et l'antenne rediffusait la priere de la veille.
cp "audio/prayers/soir_${TODAY}.mp3"   "Priere/Priere du soir/priere_soir.mp3"    2>/dev/null || true
cp "audio/testimonies/${TODAY}.mp3"    "Priere/Temoignage/temoignage.mp3"         2>/dev/null || true
cp "audio/sermons/${TODAY}.mp3"        "Sermon/sermon.mp3"                        2>/dev/null || true

# 5) Publication
git pull origin main --no-edit
git add -A
git commit -m "Contenu spirituel $(date '+%Y-%m-%d %Hh%M')"
git push origin main

echo
echo "✅ Spirituel OK"
