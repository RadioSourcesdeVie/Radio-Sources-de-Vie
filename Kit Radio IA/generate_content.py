#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Génère les prières du jour (autant de moments que défini dans
config.PRIERE_MOMENTS) et un témoignage (texte, JSON).
Moteur : Claude (config.ANTHROPIC_API_KEY). Rotation des versets/thèmes pour
éviter les répétitions d'un jour à l'autre ET entre les moments du même jour.
Usage : python generate_content.py [--type prayer|testimony|all]
"""
import sys
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from ai_text import generate_json, get_recent, save_json, verifier_config

verifier_config()

TODAY = datetime.now().strftime("%Y-%m-%d")
DAY_NUM = datetime.now().day
BASE_DIR = Path(__file__).parent.parent

BOOKS_ROTATION = {
    0: "Genèse, Exode, Lévitique",
    1: "Psaumes, Proverbes, Ecclésiaste",
    2: "Ésaïe, Jérémie, Ézéchiel",
    3: "Matthieu, Marc, Luc",
    4: "Jean, Actes, Romains",
    5: "1 Corinthiens, Éphésiens, Philippiens",
    6: "Colossiens, Hébreux, Jacques, Apocalypse",
}

THEMES_TEMOIGNAGE = [
    "la guérison après une maladie grave", "retrouver la foi après un deuil",
    "sortir de la dépression par la prière", "la conversion d'un ancien incroyant",
    "Dieu pourvoit dans la pauvreté", "le pardon après une trahison",
    "la délivrance d'une addiction", "un miracle financier inattendu",
    "la réconciliation familiale", "trouver la paix dans l'exil ou l'immigration",
    "la protection divine dans un accident", "surmonter le rejet et l'abandon",
    "la joie retrouvée après une séparation", "un jeune qui trouve sa vocation",
    "la foi d'un parent seul", "la guérison d'un mariage brisé",
    "Dieu ouvre une porte professionnelle", "la force dans la persécution",
    "retrouver l'espoir après une perte", "la transformation d'une vie brisée",
    "vivre avec une maladie chronique par la foi", "la fidélité de Dieu dans la vieillesse",
    "un enfant qui revient à Dieu", "la provision miraculeuse",
    "surmonter la peur par la confiance en Dieu", "trouver la communauté après des années de solitude",
    "la grâce de Dieu pour un cœur repentant", "un nouveau départ après des années d'attente",
    "Dieu guérit les blessures de l'enfance", "un témoignage de service et de compassion",
]

SYSTEMS = {
    "prayer": f"Tu es un pasteur chrétien évangélique qui écrit en {config.STATION_LANGUE} pour {config.PAYS_OU_COMMUNAUTE}. Tu connais toute la Bible et tu varies tes versets chaque jour.",
    "testimony": f"Tu es un chrétien qui écrit en {config.STATION_LANGUE} des témoignages variés et édifiants pour {config.PAYS_OU_COMMUNAUTE}. Chaque jour un nouveau témoignage unique.",
}


def build_prayer_prompt(moment: str, versets_du_jour_a_eviter: list) -> str:
    books = BOOKS_ROTATION[datetime.now().weekday()]
    recent = get_recent("content/prayers", f"{moment}_", "reference")
    tous_a_eviter = list(recent) + list(versets_du_jour_a_eviter)
    avoid = "\n".join(f"  - {r}" for r in tous_a_eviter) if tous_a_eviter else "  (aucun)"
    return f"""Écris une prière chrétienne du moment "{moment}" pour le {TODAY}, en {config.STATION_LANGUE}.

RÈGLES STRICTES :
1. Choisis un verset dans ces livres UNIQUEMENT : {books}
2. NE RÉPÈTE JAMAIS ces versets déjà utilisés récemment (dont ceux des autres moments de prière déjà générés aujourd'hui) :
{avoid}
3. Le titre doit être unique et créatif (pas "Prière du {moment.capitalize()}")
4. La prière doit faire 200 à 300 mots, adaptée à l'ambiance du moment "{moment}" (ex: énergique le matin, apaisante le soir)

Réponds UNIQUEMENT en JSON valide :
{{"title":"Titre créatif et unique","date":"{TODAY}","moment":"{moment}","verse":"texte complet du verset (traduction standard)","reference":"Livre Ch:V","content":"prière 200-300 mots"}}"""


def generate_prayers():
    out_dir = BASE_DIR / "content" / "prayers"
    moments = config.PRIERE_MOMENTS or ["matin"]

    if all((out_dir / f"{m}_{TODAY}.json").exists() for m in moments):
        print(f"  prières ({', '.join(moments)}): déjà générées aujourd'hui")
        return

    versets_du_jour = []
    for moment in moments:
        out_file = out_dir / f"{moment}_{TODAY}.json"
        if out_file.exists():
            print(f"  prière ({moment}): déjà générée")
            import json as _json
            versets_du_jour.append(_json.loads(out_file.read_text(encoding="utf-8")).get("reference", ""))
            continue
        print(f"  prière ({moment})...")
        data = generate_json(build_prayer_prompt(moment, versets_du_jour), system=SYSTEMS["prayer"], max_tokens=1200)
        data["moment"] = moment
        save_json(out_file, data)
        versets_du_jour.append(data.get("reference", ""))
        print(f"  -> {out_file}")


def generate_testimony():
    out_dir = BASE_DIR / "content" / "testimonies"
    out_file = out_dir / f"{TODAY}.json"
    if out_file.exists():
        print("  témoignage: déjà généré aujourd'hui")
        return

    books = BOOKS_ROTATION[datetime.now().weekday()]
    recent = get_recent("content/testimonies", "", "reference")
    avoid = "\n".join(f"  - {r}" for r in recent) if recent else "  (aucun)"
    theme = THEMES_TEMOIGNAGE[(DAY_NUM + datetime.now().month * 3) % len(THEMES_TEMOIGNAGE)]

    print(f"  témoignage (thème: {theme})...")
    prompt = f"""Écris un témoignage chrétien édifiant sur le thème : {theme}, en {config.STATION_LANGUE}.

RÈGLES STRICTES :
1. Choisis un verset dans ces livres UNIQUEMENT : {books}
2. NE RÉPÈTE JAMAIS ces versets déjà utilisés récemment :
{avoid}
3. Le titre doit être unique et refléter le thème spécifique
4. Le témoignage doit être une histoire personnelle fictive mais réaliste (250-350 mots)

Réponds UNIQUEMENT en JSON valide :
{{"title":"Titre unique du témoignage","date":"{TODAY}","verse":"texte complet du verset","reference":"Livre Ch:V","content":"témoignage 250-350 mots"}}"""
    data = generate_json(prompt, system=SYSTEMS["testimony"], max_tokens=1200)
    save_json(out_file, data)
    print(f"  -> {out_file}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", choices=["prayer", "testimony", "all"], default="all")
    args = parser.parse_args()

    print(f"\n=== {config.STATION_NOM} — Génération contenu spirituel — {TODAY} ===")
    if args.type in ("prayer", "all"):
        generate_prayers()
    if args.type in ("testimony", "all"):
        generate_testimony()
    print("Terminé.")


if __name__ == "__main__":
    main()
