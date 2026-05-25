#!/usr/bin/env python3
"""
generate_content.py — Génère prière, sermon, témoignage
Usage: python generate_content.py --api-key VOTRE_CLE_ANTHROPIC --type all
"""
import json, sys, argparse
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ImportError:
    sys.exit("pip install anthropic")

TODAY = datetime.now().strftime("%Y-%m-%d")

PROMPTS = {
    "prayer": {
        "dir": "content/prayers",
        "system": "Tu es un pasteur chrétien évangélique francophone qui s'adresse à la diaspora haïtienne au Canada.",
        "user": f"""Écris une prière chrétienne pour le {TODAY}.
Réponds UNIQUEMENT en JSON valide sans texte avant ou après:
{{"title":"Prière du {TODAY}","date":"{TODAY}","verse":"verset Louis Segond","reference":"Livre Ch:V","content":"prière 200-300 mots"}}"""
    },
    "sermon": {
        "dir": "content/sermons",
        "system": "Tu es un prédicateur chrétien évangélique francophone avec profondeur spirituelle.",
        "user": f"""Écris un court sermon pour le {TODAY}.
Réponds UNIQUEMENT en JSON valide:
{{"title":"Titre inspirant","date":"{TODAY}","verse":"texte principal Louis Segond","reference":"Livre Ch:V","content":"sermon 400-500 mots avec intro, 3 points, conclusion"}}"""
    },
    "testimony": {
        "dir": "content/testimonies",
        "system": "Tu es un chrétien qui partage un témoignage édifiant et bibliquement fondé.",
        "user": f"""Écris un témoignage chrétien édifiant pour le {TODAY}.
Réponds UNIQUEMENT en JSON valide:
{{"title":"Titre du témoignage","date":"{TODAY}","verse":"verset Louis Segond","reference":"Livre Ch:V","content":"témoignage 250-350 mots"}}"""
    }
}

def generate(client, content_type):
    cfg = PROMPTS[content_type]
    out_dir = Path(cfg["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{TODAY}.json"
    if out_file.exists():
        print(f"⏭️  {content_type}: déjà généré aujourd'hui")
        return True
    print(f"✍️  Génération {content_type}...")
    try:
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            system=cfg["system"],
            messages=[{"role":"user","content":cfg["user"]}]
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
            raw = raw.strip()
        data = json.loads(raw)
        out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅  {content_type} → {out_file}")
        return True
    except Exception as e:
        print(f"❌  {content_type}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--type", choices=["prayer","sermon","testimony","all"], default="all")
    args = parser.parse_args()
    client = anthropic.Anthropic(api_key=args.api_key)
    types = ["prayer","sermon","testimony"] if args.type == "all" else [args.type]
    ok = sum(generate(client, t) for t in types)
    print(f"\n🙏  {ok}/{len(types)} contenus générés pour {TODAY}")

if __name__ == "__main__":
    main()
