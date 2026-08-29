#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Résumés audio courts par catégorie d'actualité
(config.CATEGORIES_NEWS). Texte : Claude. Voix : fournisseur configuré.
Usage : python generate_resumes.py
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from ai_text import generate_json, save_json, verifier_config
import tts_engine

verifier_config()

TODAY = datetime.now().strftime("%Y-%m-%d")
BASE_DIR = Path(__file__).parent.parent
EXT = tts_engine.output_extension()


def get_articles(cle: str, limite: int = 5) -> str:
    f = BASE_DIR / "content" / "news" / f"{cle}_{TODAY}.json"
    if not f.exists():
        return ""
    data = json.loads(f.read_text(encoding="utf-8"))
    return "\n".join(f"- {a['title']} ({a['source']})" for a in data.get("articles", [])[:limite])


def main():
    print(f"\n=== {config.STATION_NOM} — Résumés d'actualités — {TODAY} ===\n")

    for cle, cat in config.CATEGORIES_NEWS.items():
        if not cat["flux"]:
            continue

        out_json = BASE_DIR / "content" / "resumes" / f"{cle}_{TODAY}.json"
        out_audio = BASE_DIR / f"audio/resumes/{cle}_{TODAY}.{EXT}"

        if out_json.exists() and out_audio.exists():
            print(f"{cat['label']}: déjà généré")
            continue

        print(f"{cat['label']}...")
        articles = get_articles(cle)
        if not articles:
            print("  aucun article disponible aujourd'hui, ignoré")
            continue

        try:
            prompt = f"""Écris un résumé radio attractif des {cat['label']}, en {config.STATION_LANGUE}.
Longueur selon l'importance : 60-80 mots si peu de nouvelles, 100-120 mots si normal,
150-180 mots si beaucoup de nouvelles importantes.

Articles :
{articles}

Commence par une phrase accrocheuse, couvre 2 à 3 nouvelles, termine positivement.

JSON : {{"title":"titre court attractif","date":"{TODAY}","category":"{cle}","resume":"texte du résumé"}}"""
            data = generate_json(prompt, max_tokens=600)
            save_json(out_json, data)

            texte = f"{data['title']}.\n\n{data['resume']}"
            role = cat.get("presentateur", "presentateur_a")
            kb = tts_engine.synth_to_file(texte, role, out_audio)
            print(f"  {data['title']} — {kb} KB")
        except Exception as e:
            print(f"  erreur: {e}")

    print(f"\nRésumés terminés pour {TODAY}")


if __name__ == "__main__":
    main()
