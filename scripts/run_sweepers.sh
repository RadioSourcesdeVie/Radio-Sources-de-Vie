#!/bin/bash
# Radio Sources de Vie — Sweepers "Le saviez-vous ?" (lot hebdomadaire de 3, FR + EN)
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
source .env
echo "🎙️ Sweepers — $(date '+%Hh%M')"
echo "===== SWEEPERS lancé le $(date) =====" >> "journal_taches.log"

python generate_sweepers.py --api-key "$ANTHROPIC_KEY"

git pull origin main --no-edit
git add -A
git commit -m "Sweepers $(date '+%Y-%m-%d %Hh%M')"
git push origin main
echo "✅ Sweepers OK"
