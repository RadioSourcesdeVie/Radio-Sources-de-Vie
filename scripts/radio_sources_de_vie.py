# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Script maître
Lance automatiquement le bon segment selon l'heure du jour.
Peut aussi être appelé manuellement pour forcer un segment.

Usage automatique : python radio_sources_de_vie.py
Usage manuel      : python radio_sources_de_vie.py priere_matin
                    python radio_sources_de_vie.py nouvelles_matin
                    python radio_sources_de_vie.py sermon_matin
                    python radio_sources_de_vie.py nouvelles_soir
                    python radio_sources_de_vie.py temoignage
                    python radio_sources_de_vie.py sermon_soir
                    python radio_sources_de_vie.py priere_soir

Planification quotidienne (un script séparé par segment) :
  05:00 -> priere_matin.py
  07:00 -> nouvelles_matin.py
  09:30 -> sermon_matin.py
  17:00 -> nouvelles_soir.py
  18:00 -> temoignage.py
  20:00 -> sermon_soir.py
  21:00 -> priere_soir.py
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent

PLANIFICATION = {
    (5,  0):  'priere_matin.py',
    (7,  0):  'nouvelles_matin.py',
    (9,  30): 'sermon_matin.py',
    (17, 0):  'nouvelles_soir.py',
    (18, 0):  'temoignage.py',
    (20, 0):  'sermon_soir.py',
    (21, 0):  'priere_soir.py',
}

SEGMENTS_MANUELS = {
    'priere_matin':    'priere_matin.py',
    'nouvelles_matin': 'nouvelles_matin.py',
    'sermon_matin':    'sermon_matin.py',
    'nouvelles_soir':  'nouvelles_soir.py',
    'temoignage':      'temoignage.py',
    'sermon_soir':     'sermon_soir.py',
    'priere_soir':     'priere_soir.py',
}


def lancer_segment(script: str):
    """Lance un script de segment."""
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
    """Détecte le segment à lancer selon l'heure actuelle (fenêtre de 5 min)."""
    maintenant = datetime.now()
    minutes_actuelles = maintenant.hour * 60 + maintenant.minute

    for (heure, minute), script in sorted(PLANIFICATION.items()):
        minutes_planifiees = heure * 60 + minute
        if abs(minutes_planifiees - minutes_actuelles) <= fenetre_minutes:
            return script

    return None


def afficher_planification():
    print("\nPlanification Radio Sources de Vie:")
    print("-" * 45)
    for (h, m), script in sorted(PLANIFICATION.items()):
        print(f"  {h:02d}:{m:02d}  ->  {script}")
    print()


def main():
    print("=" * 50)
    print("     RADIO SOURCES DE VIE")
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
