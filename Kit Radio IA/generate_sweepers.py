#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Sweepers "Le saviez-vous ?" avec verset biblique.
Texte : Claude. Voix : fournisseur configuré (config.TTS_PROVIDER), rôle "sweepers"
si présent dans les dictionnaires de voix, sinon "presentateur_a".

Cadence recommandée : lot de 3 -> chaque semaine ; lot de 10+ -> chaque mois
(réglable via config.SWEEPER_TAILLE_LOT).
Usage : python generate_sweepers.py
"""
import sys
import re
import json
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from ai_text import generate_json, verifier_config
import tts_engine

verifier_config()

TODAY = datetime.now().strftime("%Y-%m-%d")
BASE_DIR = Path(__file__).parent.parent
EXT = tts_engine.output_extension()
BATCH_SIZE = config.SWEEPER_TAILLE_LOT

INDEX_PATH = BASE_DIR / "content" / "sweepers" / "index.json"
BATCH_DIR = BASE_DIR / "audio" / "sweepers"
DOSSIER_RADIODJ = BASE_DIR / config.RADIODJ_DOSSIERS.get("sweepers", "Nouvelles/Sweepers")

ROLE = "sweepers" if any("sweepers" in d for d in
                          (config.EDGE_VOICES, config.ELEVENLABS_VOICES, config.GEMINI_VOICES)) else "presentateur_a"


def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return []


def save_index(index):
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def recent_references(index, limit=40):
    refs = [e["reference"] for e in index]
    return refs[-limit:] if refs else []


def gen_sweepers(n: int, avoid_refs: list) -> list:
    avoid_text = "\n".join(f"  - {r}" for r in avoid_refs) if avoid_refs else "  (aucun)"
    prompt = f"""Écris {n} sweepers radio différents pour "{config.STATION_NOM}", en {config.STATION_LANGUE}.

Chaque sweeper doit :
- Faire 8 à 12 secondes à l'oral (environ 25 à 32 mots, référence biblique incluse)
- Suivre le format : "Le saviez-vous... [observation drôle du quotidien] ? [Référence]. Vous écoutez {config.STATION_NOM}."
- Utiliser un verset biblique DIFFÉRENT des versets suivants déjà utilisés récemment :
{avoid_text}
- Être vraiment drôle/léger, jamais moquer la foi elle-même

Réponds UNIQUEMENT en JSON, une liste de {n} objets, rien d'autre avant ou après :
[{{"slug":"identifiant-court-sans-accents","reference":"Livre Ch:V","text":"texte complet du sweeper"}}]"""
    return generate_json(prompt, max_tokens=1200)


def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "sweeper"


def clear_radiodj_folder():
    if not DOSSIER_RADIODJ.exists():
        return
    removed = 0
    for f in DOSSIER_RADIODJ.glob(f"*.{EXT}"):
        f.unlink()
        removed += 1
    if removed:
        print(f"  {removed} ancien(s) fichier(s) retiré(s) de {DOSSIER_RADIODJ}")


def main():
    print(f"\n=== {config.STATION_NOM} — Sweepers (lot de {BATCH_SIZE}) — {TODAY} ===\n")
    index = load_index()
    avoid = recent_references(index)
    sweepers = gen_sweepers(BATCH_SIZE, avoid)

    DOSSIER_RADIODJ.mkdir(parents=True, exist_ok=True)
    clear_radiodj_folder()
    clips = []
    for sw in sweepers:
        slug = slugify(sw.get("slug") or sw["reference"])
        out_file = DOSSIER_RADIODJ / f"sweeper_{TODAY}_{slug}.{EXT}"
        print(f"  {sw['reference']}...")
        kb = tts_engine.synth_to_file(sw["text"], ROLE, out_file)
        print(f"  -> {out_file} ({kb} KB)")
        index.append({"slug": slug, "reference": sw["reference"], "text": sw["text"],
                       "audio_file": str(out_file), "date_added": TODAY})
        clips.append(out_file)

    save_index(index)

    backup_dir = BATCH_DIR / "archive"
    backup_dir.mkdir(parents=True, exist_ok=True)
    for c in clips:
        shutil.copy2(c, backup_dir / Path(c).name)

    print(f"\nTerminé. {len(clips)} sweepers ajoutés -> {DOSSIER_RADIODJ}")
    print(f"Historique -> {INDEX_PATH}")


if __name__ == '__main__':
    main()
