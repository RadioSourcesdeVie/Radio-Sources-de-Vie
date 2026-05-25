#!/bin/bash
cd "/c/Users/avena/Desktop/radio sources De Vie"
source .env
python auto_push.py --owm-key "$OWM_KEY" --anthropic-key "$ANTHROPIC_KEY"
python generate_sermon.py --api-key "$ANTHROPIC_KEY"
python generate_gemini.py
python generate_audio.py
git add -A
git commit -m "📻 Mise à jour — $(date '+%d/%m/%Y à %Hh%M')"
git push origin main
