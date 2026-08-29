#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Sermon long (5 sections, ~15-20 min de lecture)
Moteur : Claude. Rotation de thèmes + anti-répétition sur 7 jours.
Usage : python generate_sermon.py
"""
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from ai_text import generate_text, clean_markdown, save_json, verifier_config

verifier_config()

TODAY = datetime.now().strftime("%Y-%m-%d")
DAY_NUM = datetime.now().timetuple().tm_yday
BASE_DIR = Path(__file__).parent.parent

SERMON_THEMES = [
    "la foi", "l'espérance", "le pardon", "la persévérance dans l'épreuve", "la prière",
    "la grâce de Dieu", "l'obéissance à Dieu", "la guérison intérieure", "la paix intérieure",
    "le service et l'humilité", "la générosité", "la famille chrétienne", "la protection divine",
    "la repentance", "la joie du salut", "la patience", "le combat spirituel", "la fidélité de Dieu",
    "la vocation et le dessein de Dieu", "la libération des chaînes du passé", "la sagesse divine",
    "la reconnaissance", "la confiance en Dieu", "la résurrection et la vie nouvelle",
    "la nouvelle naissance", "le fruit de l'Esprit", "la mission de l'Église", "la crainte de Dieu",
    "la sanctification", "l'amour du prochain", "la restauration après la chute", "l'identité en Christ",
]


def get_recent_sermons(days=7):
    recent = []
    for i in range(1, days + 1):
        past = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        f = BASE_DIR / "content" / "sermons" / f"{past}.json"
        if f.exists():
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if d.get("title"):
                    recent.append(f"{d['title']} ({d.get('reference', '')})")
            except Exception:
                pass
    return recent


def main():
    out_file = BASE_DIR / "content" / "sermons" / f"{TODAY}.json"
    if out_file.exists():
        print("Sermon déjà généré pour aujourd'hui")
        return

    print(f"\n=== {config.STATION_NOM} — Sermon du jour ===")
    theme = SERMON_THEMES[DAY_NUM % len(SERMON_THEMES)]
    recent = get_recent_sermons()
    avoid = "\n".join(f"  - {r}" for r in recent) if recent else "  (aucun)"

    print("Choix du sujet et du verset...")
    sujet_raw = generate_text(
        f"""Donne un titre de sermon chrétien évangélique en {config.STATION_LANGUE} sur le thème « {theme} »
et un verset biblique qui s'y rapporte.
NE RÉPÈTE PAS ces titres/versets déjà utilisés récemment :
{avoid}
Format exact, une seule ligne : TITRE|VERSET|REFERENCE""",
        max_tokens=150,
    )
    parts = sujet_raw.strip().split("|")
    titre = parts[0].strip() if len(parts) > 0 else "Sermon du jour"
    verset = parts[1].strip() if len(parts) > 1 else ""
    reference = parts[2].strip() if len(parts) > 2 else ""
    print(f"  Sujet : {titre}")

    system = (f"Tu es un pasteur chrétien évangélique qui prêche en {config.STATION_LANGUE}, avec profondeur "
              f"biblique, exemples concrets et chaleur pastorale pour {config.PAYS_OU_COMMUNAUTE}. "
              "IMPORTANT : ne mentionne jamais un jour précis de la semaine — ce sermon peut être "
              "écouté n'importe quel jour.")

    sections_prompts = [
        f"Écris l'INTRODUCTION de ce sermon (300 mots minimum) : '{titre}'. Commence par une histoire vraie accrocheuse, présente le sujet et le verset : {verset}. Termine par une question qui engage l'auditeur.",
        f"Écris le POINT 1 de ce sermon (500 mots minimum) : '{titre}'. Premier enseignement majeur avec 2-3 exemples bibliques concrets et une histoire de vie réelle.",
        f"Écris le POINT 2 de ce sermon (500 mots minimum) : '{titre}'. Deuxième enseignement avec versets d'appui multiples, illustrations pratiques et application pour aujourd'hui.",
        f"Écris le POINT 3 de ce sermon (500 mots minimum) : '{titre}'. Troisième enseignement avec application concrète, défis pratiques pour la semaine et encouragements.",
        f"Écris la CONCLUSION de ce sermon (400 mots minimum) : '{titre}'. Histoire illustrative émouvante, résumé des trois points, appel à l'action concret et prière finale.",
    ]

    texte_complet = ""
    for i, prompt in enumerate(sections_prompts, 1):
        print(f"  Section {i}/5...")
        texte_complet += "\n\n" + generate_text(prompt, system=system, max_tokens=1000)

    texte_complet = clean_markdown(texte_complet)
    words = len(texte_complet.split())
    minutes = round(words / 150)
    print(f"  Total : {words} mots — ~{minutes} minutes de lecture")

    save_json(out_file, {
        "title": titre, "date": TODAY, "verse": verset, "reference": reference,
        "content": texte_complet.strip(), "words": words, "minutes": minutes
    })
    print(f"Sermon sauvegardé -> {out_file}")


if __name__ == "__main__":
    main()
