# -*- coding: utf-8 -*-
"""
Kit Radio IA - Script maître
Lance automatiquement le bon segment selon l'heure du jour, d'après
la planification définie dans config.py (HORAIRE).

Usage automatique : python radio_maitre.py
Usage manuel      : python radio_maitre.py priere_matin
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
import config

BASE_DIR = Path(__file__).parent
PLANIFICATION = config.HORAIRE
SEGMENTS_MANUELS = {script.replace('.py', ''): script for script in PLANIFICATION.values()}


def lancer_segment(script: str):
    chemin_script = BASE_DIR / script

    if not chemin_script.exists():
        print(f"ERREUR: script introuvable: {chemin_script}")
        sys.exit(2)

    commande = [sys.executable, str(chemin_script)]

    print(f"\nLancement: {script}")
    print(f"Heure: {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 50)

    resultat = subprocess.run(commande, cwd=str(BASE_DIR))

    if resultat.returncode == 0:
        print(f"\nSegment terminé avec succès: {script}")
    else:
        print(f"\nErreur lors de l'exécution de: {script} (code {resultat.returncode})")


def detecter_segment_actuel(fenetre_minutes: int = 5):
    maintenant = datetime.now()
    minutes_actuelles = maintenant.hour * 60 + maintenant.minute

    for (heure, minute), script in sorted(PLANIFICATION.items()):
        minutes_planifiees = heure * 60 + minute
        if abs(minutes_planifiees - minutes_actuelles) <= fenetre_minutes:
            return script

    return None


def afficher_planification():
    print(f"\nPlanification {config.STATION_NOM}:")
    print("-" * 45)
    for (h, m), script in sorted(PLANIFICATION.items()):
        print(f"  {h:02d}:{m:02d}  ->  {script}")
    print()


def main():
    print("=" * 50)
    print(f"     {config.STATION_NOM.upper()}")
    print("=" * 50)

    if len(sys.argv) >= 2:
        nom_segment = sys.argv[1].lower()

        if nom_segment not in SEGMENTS_MANUELS:
            print(f"Segment inconnu: {nom_segment}")
            print(f"Segments disponibles: {', '.join(SEGMENTS_MANUELS.keys())}")
            sys.exit(1)

        lancer_segment(SEGMENTS_MANUELS[nom_segment])
    else:
        script = detecter_segment_actuel()
        if script:
            lancer_segment(script)
        else:
            maintenant = datetime.now()
            print(f"Aucun segment programmé à {maintenant.strftime('%H:%M')}.")
            afficher_planification()


if __name__ == '__main__':
    main()
