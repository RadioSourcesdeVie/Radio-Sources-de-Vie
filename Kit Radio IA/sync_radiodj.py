#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Copie les audios du jour vers les dossiers RadioDJ
(config.RADIODJ_DOSSIERS) pour que l'AutoDJ les diffuse.
À lancer après chaque étape de génération (voir run_*.py), ou manuellement.
Usage : python sync_radiodj.py
"""
import sys
import shutil
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent))
import config
import tts_engine

BASE_DIR = Path(__file__).parent.parent
EXT = tts_engine.output_extension()
TODAY = date.today().isoformat()


def dossier_pour(cle: str, defaut_relatif: str) -> Path:
    return BASE_DIR / config.RADIODJ_DOSSIERS.get(cle, defaut_relatif)


def copier(source: Path, cle_dossier: str, nom_sortie: str, defaut_relatif: str) -> bool:
    if not source.exists():
        return False
    dest_dossier = dossier_pour(cle_dossier, defaut_relatif)
    dest_dossier.mkdir(parents=True, exist_ok=True)
    dest = dest_dossier / f"{nom_sortie}.{EXT}"
    shutil.copyfile(source, dest)
    print(f"  OK  {source.name} -> {dest}")
    return True


def main():
    print(f"=== {config.STATION_NOM} — Synchronisation RadioDJ ===")
    total = 0

    # Météo
    if copier(BASE_DIR / f"audio/meteo/{TODAY}.{EXT}", "meteo", "meteo", "Nouvelles/Meteo"):
        total += 1

    # Prières (autant de moments que configurés)
    for moment in (config.PRIERE_MOMENTS or ["matin"]):
        cle = f"priere_{moment}"
        defaut = f"Priere/Priere du {moment}"
        if copier(BASE_DIR / f"audio/prayers/{moment}_{TODAY}.{EXT}", cle, f"priere_{moment}", defaut):
            total += 1

    # Témoignage + sermon
    if copier(BASE_DIR / f"audio/testimonies/{TODAY}.{EXT}", "temoignage", "temoignage", "Priere/Temoignage"):
        total += 1
    if copier(BASE_DIR / f"audio/sermons/{TODAY}.{EXT}", "sermon", "sermon", "Sermon"):
        total += 1

    # Journal du soir
    if copier(BASE_DIR / f"audio/bulletin_soir/{TODAY}.{EXT}", "bulletin_soir", "bulletin_soir",
              "Nouvelles/Bulletin du Soir"):
        total += 1

    # Résumés par catégorie d'actualité
    for cle in config.CATEGORIES_NEWS:
        cle_dossier = f"resume_{cle}"
        defaut = f"Nouvelles/Resume {cle.capitalize()}"
        if copier(BASE_DIR / f"audio/resumes/{cle}_{TODAY}.{EXT}", cle_dossier, f"resume_{cle}", defaut):
            total += 1

    with open(BASE_DIR / "sync_radiodj.log", "a", encoding="utf-8") as f:
        f.write(f"Sync {TODAY} : {total} fichier(s)\n")

    print(f"\n{total} fichier(s) synchronisé(s).")
    print("(Les sweepers sont copiés directement dans leur dossier RadioDJ par generate_sweepers.py)")


if __name__ == "__main__":
    main()
