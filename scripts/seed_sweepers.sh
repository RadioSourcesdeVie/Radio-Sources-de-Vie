#!/bin/bash
cd "$(dirname "$0")/.." || exit 1
export PYTHONUTF8=1
echo "Generation des 3 premiers sweepers (FR + EN)..."
python seed_sweepers.py
echo ""
echo "===== TERMINE ====="
read -p "Appuyez sur Entree pour fermer cette fenetre..."
