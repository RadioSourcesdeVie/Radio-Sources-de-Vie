#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Configuration des tâches planifiées Windows
Crée une tâche Windows par entrée de config.HORAIRE (script orchestrateur).
IMPORTANT : exécuter en tant qu'administrateur pour SYSTEM, sinon utilisateur courant.
Usage : python setup_tasks.py
"""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

BASE_DIR = Path(__file__).parent

PYTHON_DIR = Path(sys.executable).parent
PYTHONW = PYTHON_DIR / 'pythonw.exe'
if not PYTHONW.exists():
    PYTHONW = Path(sys.executable)

PREFIXE_TACHE = config.STATION_NOM.replace(' ', '')

JOURS_SEMAINE = {"MON": "MON", "TUE": "TUE", "WED": "WED", "THU": "THU",
                  "FRI": "FRI", "SAT": "SAT", "SUN": "SUN"}


def parse_horaire():
    """Transforme config.HORAIRE en liste de tâches. Clé (h, m) = tous les
    jours. Clé (h, m, "JOUR") = un seul jour de la semaine (ex: "MON")."""
    taches = []
    for cle, script in config.HORAIRE.items():
        if len(cle) == 2:
            h, m = cle
            jour = None
        else:
            h, m, jour = cle
        taches.append({
            'nom': f"{PREFIXE_TACHE}_{script.replace('.py', '')}" + (f"_{jour}" if jour else ""),
            'script': script,
            'heure': f"{h:02d}:{m:02d}",
            'jour': jour,
            'description': f"{config.STATION_NOM} — {script.replace('.py', '').replace('_', ' ')} {h:02d}h{m:02d}"
        })
    return taches


TACHES = parse_horaire()


def creer_tache(tache: dict) -> bool:
    chemin_script = str(BASE_DIR / tache['script'])
    python_exe = str(PYTHONW)
    action = f'"{python_exe}" "{chemin_script}"'

    subprocess.run(['schtasks', '/delete', '/tn', tache['nom'], '/f'], capture_output=True)

    base_cmd = ['schtasks', '/create', '/tn', tache['nom'], '/tr', action, '/st', tache['heure'], '/f']
    if tache['jour']:
        cmd = base_cmd + ['/sc', 'WEEKLY', '/d', JOURS_SEMAINE.get(tache['jour'], 'MON')]
    else:
        cmd = base_cmd + ['/sc', 'DAILY']

    resultat = subprocess.run(cmd + ['/rl', 'HIGHEST', '/ru', 'SYSTEM'],
                               capture_output=True, text=True, encoding='utf-8')
    if resultat.returncode == 0:
        print(f"  OK  {tache['nom']:<45} ({tache['heure']})")
        return True

    resultat2 = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if resultat2.returncode == 0:
        print(f"  OK  {tache['nom']:<45} ({tache['heure']}) [utilisateur courant]")
        return True

    print(f"  ERR {tache['nom']}: {(resultat2.stderr or resultat.stderr).strip()[:80]}")
    return False


def main():
    print("=" * 60)
    print(f"  {config.STATION_NOM} — Configuration des tâches Windows")
    print("=" * 60)
    print(f"\nPython  : {PYTHONW}")
    print(f"Dossier : {BASE_DIR}\n")

    for tache in TACHES:
        chemin = BASE_DIR / tache['script']
        if not chemin.exists():
            print(f"AVERTISSEMENT: Script manquant: {chemin}")

    print("\nCréation des tâches planifiées...")
    print("-" * 60)
    ok = sum(creer_tache(t) for t in TACHES)

    print(f"\nRésultat: {ok}/{len(TACHES)} tâches créées avec succès.")
    if ok < len(TACHES):
        print("\nSi des tâches ont échoué, relancez ce script en tant qu'administrateur")
        print("(clic droit sur l'invite de commandes > 'Exécuter en tant qu'administrateur').")

    print("\nPlanification :")
    print("-" * 45)
    for t in TACHES:
        suffixe = f" ({t['jour']})" if t['jour'] else " (tous les jours)"
        print(f"  {t['heure']}{suffixe}  ->  {t['description']}")


if __name__ == '__main__':
    main()
