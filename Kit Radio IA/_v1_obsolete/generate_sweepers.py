#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Sweepers "Le saviez-vous ?" avec versets bibliques
Texte généré par Gemini (config.py section 4), voix par Edge TTS (Microsoft,
gratuit, sans clé API).

Cadence recommandée : lot de 3 sweepers -> régénérer CHAQUE SEMAINE.
                       lot de 10+ sweepers -> régénérer CHAQUE MOIS.
Réglable via config.SWEEPER_TAILLE_LOT.

Génère à chaque exécution :
  1) De nouveaux textes, verset différent des lots précédents
     (historique lu dans content/sweepers/index.json)
  2) Un fichier audio individuel par sweeper dans le(s) dossier(s) RadioDJ
     défini(s) dans config.py (RadioDJ les fait tourner au hasard)
  3) Une copie de sauvegarde dans audio/sweepers/
  4) Mise à jour de content/sweepers/index.json (historique anti-répétition)

Usage : python generate_sweepers.py
"""
import sys
import asyncio
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from utils import BASE_DIR, generate_text, verifier_config

verifier_config()

import edge_tts

TODAY = datetime.now().strftime("%Y-%m-%d")
BATCH_SIZE = config.SWEEPER_TAILLE_LOT

INDEX_PATH = BASE_DIR / "content" / "sweepers" / "index.json"
BATCH_DIR = BASE_DIR / "audio" / "sweepers"

LANGUES = [("principale", config.STATION_LANGUE, config.SWEEPER_VOIX_PRINCIPALE,
            BASE_DIR / config.SWEEPER_DOSSIER_PRINCIPAL)]
if config.SWEEPER_LANGUE_SECONDAIRE:
    LANGUES.append(("secondaire", config.SWEEPER_LANGUE_SECONDAIRE,
                     config.SWEEPER_VOIX_SECONDAIRE, BASE_DIR / config.SWEEPER_DOSSIER_SECONDAIRE))


def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return []


def save_index(index):
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def recent_references(index, cle_langue, limit=40):
    refs = [e["reference"] for e in index if e.get("langue") == cle_langue]
    return refs[-limit:] if refs else []


def gen_sweepers(langue: str, n: int, avoid_refs: list) -> list:
    avoid_text = "\n".join(f"  - {r}" for r in avoid_refs) if avoid_refs else "  (aucun)"
    prompt = f"""Écris {n} sweepers radio différents pour "{config.STATION_NOM}", en {langue}.

Chaque sweeper doit :
- Faire 8 à 12 secondes à l'oral (environ 25 à 32 mots, référence biblique incluse)
- Suivre le format : "Le saviez-vous... [observation drôle du quotidien] ? [Référence]. Vous écoutez {config.STATION_NOM}."
- Utiliser un verset biblique DIFFÉRENT des versets suivants déjà utilisés récemment :
{avoid_text}
- Être vraiment drôle/léger, pas juste une info biblique sèche
- Ne jamais moquer la foi elle-même — la blague porte sur la vie de tous les jours

Réponds UNIQUEMENT en JSON, une liste de {n} objets, rien d'autre avant ou après :
[{{"slug":"identifiant-court-sans-accents","reference":"Livre Ch:V","text":"texte complet du sweeper"}}]"""

    raw = generate_text(prompt).strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    start = raw.find("[")
    data, _ = json.JSONDecoder().raw_decode(raw[start:])
    return data


def clean_reference(text: str) -> str:
    """"Philippiens 4:6" -> "Philippiens 4 verset 6" (sinon la voix lit ça comme une heure)."""
    text = re.sub(r'(\d+):(\d+)-(\d+)', r'\1 verset \2 à \3', text)
    text = re.sub(r'(\d+):(\d+)', r'\1 verset \2', text)
    return text


async def _synth_bytes(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)


def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "sweeper"


def clear_radiodj_folder(out_dir: Path):
    """Vide le dossier RadioDJ avant d'y déposer le nouveau lot — RadioDJ ne
    doit jamais avoir un mélange d'anciens et de nouveaux sweepers. L'archive
    (audio/sweepers) n'est JAMAIS vidée, elle garde tout l'historique."""
    if not out_dir.exists():
        return
    removed = 0
    for f in out_dir.glob("*.mp3"):
        f.unlink()
        removed += 1
    if removed:
        print(f"  {removed} ancien(s) fichier(s) retiré(s) de {out_dir}")


def synth_langue(sweepers, cle_langue, voice, out_dir: Path, index):
    out_dir.mkdir(parents=True, exist_ok=True)
    clear_radiodj_folder(out_dir)
    clips = []
    for sw in sweepers:
        slug = slugify(sw.get("slug") or sw["reference"])
        out_file = out_dir / f"sweeper_{cle_langue}_{TODAY}_{slug}.mp3"
        print(f"  {cle_langue} — {sw['reference']}...")
        texte = clean_reference(sw["text"])
        audio = asyncio.run(_synth_bytes(texte, voice))
        out_file.write_bytes(audio)
        print(f"  -> {out_file} ({len(audio)//1024} KB)")
        index.append({
            "langue": cle_langue,
            "slug": slug,
            "reference": sw["reference"],
            "text": sw["text"],
            "audio_file": str(out_file).replace("\\", "/"),
            "date_added": TODAY,
        })
        clips.append(out_file)
    return clips


def copy_backup_clips(clips, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for c in clips:
        shutil.copy2(c, out_dir / Path(c).name)
    print(f"  Copie de sauvegarde ({len(clips)} fichiers) -> {out_dir}")


def main():
    print(f"\n=== {config.STATION_NOM} — Génération du lot de sweepers ({BATCH_SIZE}) — {TODAY} ===\n")
    index = load_index()

    for cle, langue, voix, dossier in LANGUES:
        avoid = recent_references(index, cle)
        sweepers = gen_sweepers(langue, BATCH_SIZE, avoid)
        clips = synth_langue(sweepers, cle, voix, dossier, index)
        copy_backup_clips(clips, BATCH_DIR / cle)

    save_index(index)
    print(f"\nTerminé. Historique -> {INDEX_PATH}")


if __name__ == '__main__':
    main()
