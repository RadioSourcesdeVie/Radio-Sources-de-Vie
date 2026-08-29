# -*- coding: utf-8 -*-
"""Petit utilitaire partagé par les scripts run_*.py (journalisation)."""
import sys
import subprocess
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOG_FILE = BASE_DIR / "journal_taches.log"


def log(etape: str):
    ligne = f"===== {etape} lancé le {datetime.now().strftime('%a %d %b %Y %H:%M:%S')} ====="
    print(ligne)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(ligne + "\n")


def lancer(script: str, *args):
    chemin = Path(__file__).parent / script
    cmd = [sys.executable, str(chemin), *args]
    print(f"\n--- {script} {' '.join(args)} ---")
    resultat = subprocess.run(cmd, cwd=str(Path(__file__).parent))
    if resultat.returncode != 0:
        print(f"AVERTISSEMENT: {script} a retourné le code {resultat.returncode}")
    return resultat.returncode == 0
