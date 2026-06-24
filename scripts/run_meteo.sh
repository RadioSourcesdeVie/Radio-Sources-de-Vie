#!/bin/bash
cd "/c/Users/avena/Desktop/radio sources De Vie"
export PYTHONUTF8=1
source .env
TODAY=$(date '+%Y-%m-%d')
echo "🌡️ Météo — $(date '+%Hh%M')"
python fetch_weather.py --api-key "$OWM_KEY"
rm -f "content/meteo/${TODAY}.json"
rm -f "audio/meteo/${TODAY}.mp3"
python generate_daily_audio.py --eleven-key "$ELEVEN_KEY"
python generate_rss.py --type meteo
cp "audio/meteo/${TODAY}.mp3" "Nouvelles/Radio SDV Meteo/meteo.mp3" 2>/dev/null || true
cp "audio/prayers/matin_${TODAY}.mp3" "Priere/Priere du matin/priere_matin.mp3" 2>/dev/null || true
cp "audio/prayers/soir_${TODAY}.mp3" "Priere/Priere du soir/priere_soir.mp3" 2>/dev/null || true
cp "audio/testimonies/${TODAY}.mp3" "Priere/Temoignage/temoignage.mp3" 2>/dev/null || true
git pull origin main --no-edit
git add -A
git commit -m "Météo $(date '+%Hh%M')"
git push origin main
echo "✅ Météo OK"
