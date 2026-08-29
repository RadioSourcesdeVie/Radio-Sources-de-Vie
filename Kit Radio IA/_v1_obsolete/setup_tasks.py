# -*- coding: utf-8 -*-
"""
Kit Radio IA - Configuration des tâches planifiées Windows
Crée une tâche Windows par segment défini dans config.py (HORAIRE).
IMPORTANT: Exécuter en tant qu'administrateur pour SYSTEM, sinon utilisateur courant.
Usage: python setup_tasks.py
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

TACHES = [
    {
        'nom':         f"{PREFIXE_TACHE}_{script.replace('.py', '')}",
        'script':      script,
        'heure':       f"{h:02d}:{m:02d}",
        'description': f"{config.STATION_NOM} — {script.replace('.py', '').replace('_', ' ')} {h:02d}h{m:02d}"
    }
    for (h, m), script in sorted(config.HORAIRE.items())
]


def creer_tache(tache: dict) -> bool:
    chemin_script = str(BASE_DIR / tache['script'])
    python_exe = str(PYTHONW)
    action = f'"{python_exe}" "{chemin_script}"'

    subprocess.run(
        ['schtasks', '/delete', '/tn', tache['nom'], '/f'],
        capture_output=True
    )

    cmd = [
        'schtasks', '/create',
        '/tn',  tache['nom'],
        '/tr',  action,
        '/sc',  'DAILY',
        '/st',  tache['heure'],
        '/f',
        '/rl',  'HIGHEST',
        '/ru',  'SYSTEM'
    ]
    resultat = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

    if resultat.returncode == 0:
        print(f"  OK  {tache['nom']:<45} ({tache['heure']})")
        return True

    cmd_user = [
        'schtasks', '/create',
        '/tn', tache['nom'],
        '/tr', action,
        '/sc', 'DAILY',
        '/st', tache['heure'],
        '/f'
    ]
    resultat2 = subprocess.run(cmd_user, capture_output=True, text=True, encoding='utf-8')
    if resultat2.returncode == 0:
        print(f"  OK  {tache['nom']:<45} ({tache['heure']}) [utilisateur courant]")
        return True

    print(f"  ERR {tache['nom']}: {(resultat2.stderr or resultat.stderr).strip()[:80]}")
    return False


def verifier_taches():
    print("\nVérification des tâches créées:")
    print("-" * 55)
    for tache in TACHES:
        resultat = subprocess.run(
            ['schtasks', '/query', '/tn', tache['nom'], '/fo', 'LIST'],
            capture_output=True, text=True, encoding='utf-8', errors='replace'
        )
        if resultat.returncode == 0:
            for ligne in resultat.stdout.splitlines():
                if 'tat' in ligne or 'Status' in ligne or 'Statut' in ligne:
                    print(f"  {tache['nom'][:40]:<40} {ligne.split(':', 1)[-1].strip()}")
                    break
        else:
            print(f"  {tache['nom'][:40]:<40} NON TROUVÉE")


def main():
    print("=" * 60)
    print(f"  {config.STATION_NOM} — Configuration des tâches Windows")
    print("=" * 60)
    print(f"\nPython  : {PYTHONW}")
    print(f"Dossier : {BASE_DIR}")
    print()

    for tache in TACHES:
        chemin = BASE_DIR / tache['script']
        if not chemin.exists():
            print(f"AVERTISSEMENT: Script manquant: {chemin}")

    print("\nCréation des tâches planifiées...")
    print("-" * 60)

    ok = 0
    for tache in TACHES:
        if creer_tache(tache):
            ok += 1

    print()
    print(f"Résultat: {ok}/{len(TACHES)} tâches créées avec succès.")

    if ok < len(TACHES):
        print("\nATTENTION: Certaines tâches n'ont pas pu être créées.")
        print("Solutions possibles:")
        print("  1. Exécuter ce script en tant qu'administrateur")
        print("  2. Clic droit sur l'invite de commandes -> 'Exécuter en tant qu'administrateur'")
    else:
        print("\nToutes les tâches ont été créées avec succès!")

    print("\nPlanification quotidienne:")
    print("-" * 45)
    for tache in TACHES:
        print(f"  {tache['heure']}  ->  {tache['description']}")

    verifier_taches()


if __name__ == '__main__':
    main()
