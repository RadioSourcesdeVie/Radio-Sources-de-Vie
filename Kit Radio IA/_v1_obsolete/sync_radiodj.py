# -*- coding: utf-8 -*-
"""
Kit Radio IA - Synchronisation des audios générés vers les dossiers RadioDJ
Copie le dernier fichier audio de chaque segment vers le dossier RadioDJ
correspondant, défini dans config.py (RADIODJ_DOSSIERS), afin que l'AutoDJ
puisse le diffuser. À planifier juste après chaque génération, ou à lancer
manuellement.
Usage : python sync_radiodj.py
"""
import sys
import shutil
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
import config

BASE_DIR = Path(__file__).parent.parent

# Association: dossier de sortie des scripts -> clé RADIODJ_DOSSIERS -> nom de fichier RadioDJ
CORRESPONDANCES = [
    ("nouvelles",  "resume_local",    "resume_local.mp3"),
    ("nouvelles",  "resume_monde",    "resume_monde.mp3"),
    ("nouvelles",  "resume_chretien", "resume_chretien.mp3"),
    ("priere",     "priere_matin",    "priere_matin.mp3"),
    ("priere",     "priere_soir",     "priere_soir.mp3"),
    ("temoignage", "temoignage",      "temoignage.mp3"),
]


def dernier_fichier(dossier: Path, motif: str):
    fichiers = sorted(dossier.glob(f"{motif}*.wav"), reverse=True)
    return fichiers[0] if fichiers else None


def main():
    print(f"=== {config.STATION_NOM} — Synchronisation RadioDJ ===")
    aujourdhui = date.today().isoformat()
    total_ok = 0

    for source_dossier, cle_radiodj, nom_sortie in CORRESPONDANCES:
        if cle_radiodj not in config.RADIODJ_DOSSIERS:
            continue
        dossier_src = BASE_DIR / source_dossier
        if not dossier_src.exists():
            continue

        fichier = dernier_fichier(dossier_src, cle_radiodj.split('_')[-1])
        if not fichier:
            # fallback: prendre le fichier le plus récent du dossier
            candidats = sorted(dossier_src.glob("*.wav"), reverse=True)
            fichier = candidats[0] if candidats else None
        if not fichier:
            print(f"  (rien à synchroniser pour {cle_radiodj})")
            continue

        dossier_dest = BASE_DIR / config.RADIODJ_DOSSIERS[cle_radiodj]
        dossier_dest.mkdir(parents=True, exist_ok=True)
        destination = dossier_dest / nom_sortie

        shutil.copyfile(fichier, destination)
        print(f"  OK  {fichier.name} -> {destination}")
        total_ok += 1

    with open(BASE_DIR / "sync_radiodj.log", "a", encoding="utf-8") as f:
        f.write(f"Sync {aujourdhui} : {total_ok} fichier(s)\n")

    print(f"\n{total_ok} fichier(s) synchronisé(s).")


if __name__ == "__main__":
    main()
