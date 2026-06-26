#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
echo "===== NEWS lancé le $(date) — copie démarrée =====" >> "/c/Users/avena/Desktop/Radio Sources De Vie/journal_taches.log"
source .env
echo "📰 Nouvelles — $(date '+%Hh%M')"
python fetch_news.py
python generate_gemini.py
python generate_resumes.py --api-key "$ANTHROPIC_KEY" --eleven-key "$ELEVEN_KEY"
python generate_rss.py --type news
cp "audio/resumes/haiti_$(date '+%Y-%m-%d').mp3" "Nouvelles/Radio SDV Nouvelle Haïti/resume_haiti.mp3" 2>/dev/null || true
cp "audio/resumes/monde_$(date '+%Y-%m-%d').mp3" "Nouvelles/Radio SDV Nouvelle du Monde/resume_monde.mp3" 2>/dev/null || true
cp "audio/resumes/chretien_$(date '+%Y-%m-%d').mp3" "Nouvelles/Radio SDV Nouvelle Chretienne/resume_chretien.mp3" 2>/dev/null || true
cp "audio/resumes/sport_$(date '+%Y-%m-%d').mp3" "Nouvelles/Radio SDV Nouvelle Sport/resume_sport.mp3" 2>/dev/null || true
git pull origin main --no-edit
git add -A
git commit -m "News $(date '+%Hh%M')"
git push origin main
echo "✅ Nouvelles OK"
