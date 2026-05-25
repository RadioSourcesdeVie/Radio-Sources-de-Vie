#!/bin/bash
cd "/c/Users/avena/Desktop/radio sources De Vie"
source .env
echo "📻 Radio Sources de Vie — $(date '+%d/%m/%Y a %Hh%M')"
python fetch_weather.py --api-key "$OWM_KEY"
python fetch_news.py
python generate_content.py --api-key "$ANTHROPIC_KEY" --type all
python generate_sermon.py --api-key "$ANTHROPIC_KEY"
python generate_daily.py --api-key "$ANTHROPIC_KEY"
python generate_gemini.py
python generate_resumes.py --api-key "$ANTHROPIC_KEY" --eleven-key "$ELEVEN_KEY"
python generate_audio.py
python generate_rss.py
git add -A
git commit -m "Radio $(date '+%d/%m/%Y %Hh%M')"
git push origin main
echo "OK - Site mis a jour"
