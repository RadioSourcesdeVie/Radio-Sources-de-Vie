#!/bin/bash
cd "/c/Users/avena/Desktop/radio sources De Vie"
source .env
echo "📰 Nouvelles — $(date '+%Hh%M')"
python fetch_news.py
python generate_gemini.py
python generate_resumes.py --api-key "$ANTHROPIC_KEY" --eleven-key "$ELEVEN_KEY"
python generate_rss.py --type news
cp "audio/resumes/haiti_$(date '+%Y-%m-%d').mp3" "Nouvelles/resume_haiti.mp3"
cp "audio/resumes/monde_$(date '+%Y-%m-%d').mp3" "Nouvelles/resume_monde.mp3"
cp "audio/resumes/chretien_$(date '+%Y-%m-%d').mp3" "Nouvelles/resume_chretien.mp3"
cp "audio/resumes/sport_$(date '+%Y-%m-%d').mp3" "Nouvelles/resume_sport.mp3"
git pull origin main --no-edit
git add -A
git commit -m "News $(date '+%Hh%M')"
git push origin main
echo "✅ Nouvelles OK"