#!/usr/bin/env python3
"""
generate_resumes.py — Résumés audio Charlotte pour chaque catégorie
Radio Sources de Vie Chrétienne
"""
import anthropic, json, requests, argparse
from datetime import datetime
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")

CATEGORIES = [
    {"key":"chretien","icon":"✝️","desc":"pour la communauté chrétienne mondiale","system":"Tu es Charlotte, présentatrice radio chrétienne francophone chaleureuse."},
    {"key":"haiti",   "icon":"🇭🇹","desc":"pour la diaspora haïtienne à Ottawa","system":"Tu es Charlotte, présentatrice radio francophone pour la diaspora haïtienne."},
    {"key":"monde",   "icon":"🌍","desc":"pour nos auditeurs francophones","system":"Tu es Charlotte, présentatrice radio francophone internationale."},
    {"key":"sport",   "icon":"⚽","desc":"sportives du jour","system":"Tu es Charlotte, présentatrice radio sport francophone dynamique et enthousiaste."},
]

def get_articles(category):
    try:
        data = json.loads(Path(f"content/news/{category}_{TODAY}.json").read_text(encoding="utf-8"))
        return "\n".join([f"- {a['title']} ({a['source']})" for a in data.get("articles",[])[:5]])
    except: return "Nouvelles indisponibles"

def tts(text, out_path, eleven_key):
    MODEL = "eleven_multilingual_v2"
    CHARLOTTE = "EXAVITQu4vr4xnSDxMaL"
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{CHARLOTTE}",
        headers={"xi-api-key": eleven_key, "Content-Type": "application/json"},
        json={"text": text[:4500], "model_id": MODEL,
              "voice_settings": {"stability":0.65,"similarity_boost":0.8}}, timeout=60)
    r.raise_for_status()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(r.content)
    return Path(out_path).stat().st_size // 1024

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key",    required=True, help="Clé Anthropic")
    parser.add_argument("--eleven-key", required=True, help="Clé ElevenLabs")
    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    print(f"\n📻 Génération résumés audio — {TODAY}\n")

    for cat in CATEGORIES:
        out_json = Path(f"content/resumes/{cat['key']}_{TODAY}.json")
        out_mp3  = Path(f"audio/resumes/{cat['key']}_{TODAY}.mp3")

        if out_json.exists() and out_mp3.exists():
            print(f"⏭️  {cat['icon']} {cat['key']}: déjà généré")
            continue

        print(f"📻 {cat['icon']} {cat['key']}...")
        articles = get_articles(cat['key'])

        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=400,
                system=cat['system'],
                messages=[{"role":"user","content":f"""Écris un résumé radio ATTRACTIF 60-80 mots {cat['desc']}.
Articles:
{articles}
Commence par phrase accrocheuse, 2-3 nouvelles, termine positivement.
JSON: {{"title":"titre court attractif","date":"{TODAY}","category":"{cat['key']}","resume":"texte 60-80 mots"}}"""}]
            )
            raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
            d = json.loads(raw)
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            kb = tts(f"{d['title']}.\n\n{d['resume']}", str(out_mp3), args.eleven_key)
            print(f"✅ {d['title']} — {kb} KB")
        except Exception as e:
            print(f"❌ {cat['key']}: {e}")

    print(f"\n✅ Résumés terminés pour {TODAY}")

if __name__ == "__main__":
    main()
