#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
TODAY=$(date '+%Y-%m-%d')
cp "audio/meteo/${TODAY}.mp3" "Nouvelles/Radio SDV Meteo/meteo.mp3" 2>/dev/null
cp "audio/resumes/haiti_${TODAY}.mp3" "Nouvelles/Radio SDV Nouvelle Haïti/resume_haiti.mp3" 2>/dev/null
cp "audio/resumes/monde_${TODAY}.mp3" "Nouvelles/Radio SDV Nouvelle du Monde/resume_monde.mp3" 2>/dev/null
cp "audio/resumes/chretien_${TODAY}.mp3" "Nouvelles/Radio SDV Nouvelle Chretienne/resume_chretien.mp3" 2>/dev/null
cp "audio/resumes/sport_${TODAY}.mp3" "Nouvelles/Radio SDV Nouvelle Sport/resume_sport.mp3" 2>/dev/null
cp "audio/prayers/matin_${TODAY}.mp3" "Priere/Priere du matin/priere_matin.mp3" 2>/dev/null
cp "audio/prayers/soir_${TODAY}.mp3" "Priere/Priere du soir/priere_soir.mp3" 2>/dev/null
cp "audio/testimonies/${TODAY}.mp3" "Priere/Temoignage/temoignage.mp3" 2>/dev/null
echo "Sync $(date)" >> sync_radiodj.log
