#!/bin/bash
cd "/c/Users/avena/Desktop/radio sources De Vie"
source .env
TODAY=$(date '+%Y-%m-%d')
echo "🌡️ Météo — $(date '+%Hh%M')"
python fetch_weather.py --api-key "$OWM_KEY"
# Supprimer ancien JSON et MP3 pour forcer régénération
rm -f "content/meteo/${TODAY}.json"
rm -f "audio/meteo/${TODAY}.mp3"
python generate_daily_audio.py --eleven-key "$ELEVEN_KEY"
python generate_rss.py --type meteo
git pull origin main --no-edit
git add -A
git commit -m "Météo $(date '+%Hh%M')"
git push origin main
echo "✅ Météo OK"
