#!/usr/bin/env python3
"""
generate_daily.py — Prière matin+soir, Sabbat Nugget
Radio Sources de Vie Chrétienne
"""
import anthropic, json
from datetime import datetime
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")
HOUR  = datetime.now().hour

SYSTEM_PASTOR = "Tu es un pasteur chrétien évangélique francophone pour la diaspora haïtienne au Canada. Langue: français uniquement."

def gen(client, prompt, system=SYSTEM_PASTOR, max_tokens=1500):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role":"user","content":prompt}]
    )
    return msg.content[0].text.strip()

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def generate_prayer_matin(client):
    out = f"content/prayers/matin_{TODAY}.json"
    if Path(out).exists(): print("⏭️  Prière matin déjà générée"); return
    print("🌅 Prière matin...")
    raw = gen(client, f"""Écris une prière du matin pour le {TODAY} en français.
JSON uniquement: {{"title":"Prière du Matin — {TODAY}","date":"{TODAY}","moment":"matin","verse":"verset Louis Segond","reference":"Livre Ch:V","content":"prière 150-200 mots pour commencer la journée avec Dieu"}}""")
    raw = raw.replace("```json","").replace("```","").strip()
    save(out, json.loads(raw))
    print(f"✅ Prière matin → {out}")

def generate_prayer_soir(client):
    out = f"content/prayers/soir_{TODAY}.json"
    if Path(out).exists(): print("⏭️  Prière soir déjà générée"); return
    print("🌙 Prière soir...")
    raw = gen(client, f"""Écris une prière du soir pour le {TODAY} en français.
JSON uniquement: {{"title":"Prière du Soir — {TODAY}","date":"{TODAY}","moment":"soir","verse":"verset Louis Segond","reference":"Livre Ch:V","content":"prière 150-200 mots de remerciement et paix pour la nuit"}}""")
    raw = raw.replace("```json","").replace("```","").strip()
    save(out, json.loads(raw))
    print(f"✅ Prière soir → {out}")

def generate_sabbat_nugget(client):
    out = f"content/sabbat/{TODAY}.json"
    if Path(out).exists(): print("⏭️  Sabbat Nugget déjà généré"); return
    print("🕯️  Sabbat Nugget...")
    raw = gen(client, f"""Écris un Sabbat Nugget (méditation biblique courte) pour le {TODAY} en français.
JSON uniquement: {{"title":"Sabbat Nugget — {TODAY}","date":"{TODAY}","verse":"verset Louis Segond","reference":"Livre Ch:V","content":"méditation courte 100-150 mots, profonde et apaisante, sur le repos en Dieu"}}""")
    raw = raw.replace("```json","").replace("```","").strip()
    save(out, json.loads(raw))
    print(f"✅ Sabbat Nugget → {out}")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    args = parser.parse_args()
    client = anthropic.Anthropic(api_key=args.api_key)
    
    print(f"\n📻 Génération contenu quotidien — {TODAY}\n")
    generate_prayer_matin(client)
    generate_prayer_soir(client)
    generate_sabbat_nugget(client)
    print(f"\n✅ Tout généré pour {TODAY}")

if __name__ == "__main__":
    main()
