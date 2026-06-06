#!/bin/bash
cd "/c/Users/avena/Desktop/radio sources De Vie"
source .env
echo "🌡️ Météo — $(date '+%Hh%M')"
python fetch_weather.py --api-key "$OWM_KEY"
python generate_audio.py --type meteo
python generate_rss.py --type meteo
git pull origin main --no-edit
git add -A
git commit -m "Météo $(date '+%Hh%M')"
git push origin main
echo "✅ Météo OK"
