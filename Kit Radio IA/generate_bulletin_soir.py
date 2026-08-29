#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Journal du soir complet (10-15 min), compilé à partir des
catégories d'actualités déjà collectées dans la journée (fetch_news.py).
Texte : Claude. Voix : duo presentateur_a / presentateur_b (fournisseur configuré).
Usage : python generate_bulletin_soir.py
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from ai_text import generate_text, save_json, load_json, verifier_config
import tts_engine

verifier_config()

TODAY = datetime.now().strftime("%Y-%m-%d")
BASE_DIR = Path(__file__).parent.parent
EXT = tts_engine.output_extension()

SYSTEM = (f"Tu écris pour le journal du soir de {config.STATION_NOM}, une radio chrétienne pour "
          f"{config.PAYS_OU_COMMUNAUTE}, co-présenté par deux voix. Ton style : professionnel, "
          f"chaleureux, clair, jamais robotique ni une liste de titres. Réponds en {config.STATION_LANGUE}.")


def get_articles(cle: str, limit: int = 6):
    f = BASE_DIR / "content" / "news" / f"{cle}_{TODAY}.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text(encoding="utf-8"))
    arts = data.get("articles", [])[:limit]
    if not arts:
        return None
    return "\n".join(f"- {a['title']} ({a.get('source', '')}) — {(a.get('desc') or '').strip()}" for a in arts)


def gen_section(label: str, articles_text):
    if not articles_text:
        return f"Pas d'actualité {label.lower()} particulière à signaler aujourd'hui."
    prompt = f"""Écris la section "{label}" du journal du soir ({TODAY}) pour {config.STATION_NOM}.

Voici les vraies informations disponibles aujourd'hui (titre, source, résumé) :
{articles_text}

Consignes :
- 300 à 400 mots
- Style journal radio parlé, fluide, jamais une liste de titres collés
- Mentionne explicitement 2 à 4 sources par leur nom pour la crédibilité
- Reste fidèle aux faits donnés ci-dessus, n'invente aucun fait
- Commence par une transition naturelle
- Aucun symbole markdown (pas de **, pas de #, pas de _)"""
    return generate_text(prompt, system=SYSTEM, max_tokens=900)


def main():
    out_json = BASE_DIR / "content" / "bulletin_soir" / f"{TODAY}.json"
    out_audio = BASE_DIR / f"audio/bulletin_soir/{TODAY}.{EXT}"

    if out_json.exists() and out_audio.exists():
        print("Journal du soir déjà généré aujourd'hui")
        return

    print(f"\n=== {config.STATION_NOM} — Journal du Soir — {TODAY} ===\n")

    now_h = datetime.now().strftime("%Hh%M")
    intro = f"Bonsoir chers auditeurs, il est {now_h}. Bienvenue au journal du soir de {config.STATION_NOM}. Voici les nouvelles de votre journée."
    outro = (f"Voilà qui conclut notre journal du soir. Merci de nous avoir suivi. "
             f"Nous vous retrouvons demain, à la même heure, sur {config.STATION_NOM}.")

    categories = [(cle, cat) for cle, cat in config.CATEGORIES_NEWS.items() if cat["flux"]]

    data = load_json(out_json)
    if data is None:
        sections = []
        for cle, cat in categories:
            print(f"  {cat['label']}...")
            articles_text = get_articles(cle)
            texte = gen_section(cat['label'], articles_text)
            sections.append({"key": cle, "label": cat['label'], "role": cat.get("presentateur", "presentateur_a"),
                              "text": texte})

        full_text = intro + "\n\n" + "\n\n".join(s["text"] for s in sections) + "\n\n" + outro
        words = len(full_text.split())
        data = {"date": TODAY, "title": f"Journal du Soir — {TODAY}", "intro": intro,
                "sections": sections, "outro": outro, "content": full_text,
                "words": words, "minutes": round(words / 150, 1)}
        save_json(out_json, data)
        print(f"Texte généré — {data['words']} mots (~{data['minutes']} min)")
    else:
        print("Texte déjà généré, passage direct à l'audio")

    if not out_audio.exists():
        print("Synthèse vocale (duo)...")
        segments = [(data["intro"], "presentateur_a")]
        for s in data["sections"]:
            segments.append((s["text"], s.get("role", "presentateur_a")))
        segments.append((data["outro"], "presentateur_a"))
        kb = tts_engine.synth_duo_to_file(segments, out_audio)
        print(f"Audio -> {out_audio} ({kb} KB)")
    else:
        print("Audio déjà généré")


if __name__ == "__main__":
    main()
