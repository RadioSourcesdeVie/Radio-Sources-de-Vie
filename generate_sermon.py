#!/usr/bin/env python3
"""
generate_sermon.py — Sermon 20min en sections multiples
Radio Sources de Vie Chrétienne — Audio produit manuellement
"""
import anthropic, json
from datetime import datetime
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")

def generate_sermon(api_key):
    client = anthropic.Anthropic(api_key=api_key)
    out_file = Path(f"content/sermons/{TODAY}.json")
    
    if out_file.exists():
        print(f"⏭️  Sermon déjà généré pour aujourd'hui")
        return True

    print("✍️  Génération sermon 20min...")

    # Sujet
    sujet_msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{"role":"user","content":"Donne un titre de sermon chrétien évangélique en français et un verset (Louis Segond). Format exact: TITRE|VERSET|REFERENCE"}]
    )
    parts = sujet_msg.content[0].text.strip().split("|")
    titre     = parts[0].strip() if len(parts)>0 else "Sermon du jour"
    verset    = parts[1].strip() if len(parts)>1 else ""
    reference = parts[2].strip() if len(parts)>2 else ""
    print(f"   Sujet: {titre}")

    SYSTEM = "Tu es un pasteur chrétien évangélique francophone. Tu prêches avec profondeur biblique, exemples concrets et chaleur pastorale pour la diaspora haïtienne au Canada."

    sections_prompts = [
        f"Écris l'INTRODUCTION de ce sermon (300 mots minimum): '{titre}'. Commence par une histoire vraie accrocheuse, présente le sujet et le verset: {verset}. Termine l'introduction par une question qui engage l'auditeur.",
        f"Écris le POINT 1 de ce sermon (500 mots minimum): '{titre}'. Premier enseignement majeur avec 2-3 exemples bibliques concrets et une histoire de vie réelle de la diaspora haïtienne.",
        f"Écris le POINT 2 de ce sermon (500 mots minimum): '{titre}'. Deuxième enseignement avec versets d'appui multiples, illustrations pratiques et application pour aujourd'hui.",
        f"Écris le POINT 3 de ce sermon (500 mots minimum): '{titre}'. Troisième enseignement avec application concrète, défis pratiques pour la semaine et encouragements.",
        f"Écris la CONCLUSION de ce sermon (400 mots minimum): '{titre}'. Histoire illustrative émouvante, résumé des 3 points, appel à l'action concret et prière finale.",
    ]

    texte_complet = ""
    for i, prompt in enumerate(sections_prompts):
        print(f"   Section {i+1}/5...")
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1000,
            system=SYSTEM,
            messages=[{"role":"user","content":prompt}]
        )
        texte_complet += "\n\n" + msg.content[0].text.strip()

    words   = len(texte_complet.split())
    minutes = round(words/150)
    print(f"   Total: {words} mots — ~{minutes} minutes de lecture")

    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps({
        "title": titre, "date": TODAY,
        "verse": verset, "reference": reference,
        "content": texte_complet.strip(),
        "words": words, "minutes": minutes
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅  Sermon sauvegardé → {out_file}")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()
    generate_sermon(args.api_key)
