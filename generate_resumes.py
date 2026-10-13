#!/usr/bin/env python3
"""
generate_resumes.py — Resumes audio pour chaque categorie
Radio Sources de Vie Chretienne
Voix: gTTS (Google, gratuit, sans cle API)
"""
import anthropic, json, argparse, re
from datetime import datetime
from pathlib import Path
from gtts import gTTS

TODAY = datetime.now().strftime("%Y-%m-%d")

CATEGORIES = [
    {"key":"chretien","desc":"pour la communaute chretienne mondiale","system":"Tu es Charline, presentatrice radio chretienne francophone chaleureuse."},
    {"key":"haiti",   "desc":"pour la diaspora haitienne a Ottawa",  "system":"Tu es Charline, presentatrice radio francophone pour la diaspora haitienne."},
    {"key":"monde",   "desc":"pour nos auditeurs francophones",       "system":"Tu es Antoine, presentateur radio francophone international."},
    {"key":"sport",   "desc":"sportives du jour",                     "system":"Tu es Antoine, presentateur radio sport francophone dynamique et enthousiaste."},
]

def get_articles(category):
    try:
        data = json.loads(Path(f"content/news/{category}_{TODAY}.json").read_text(encoding="utf-8"))
        return "\n".join([f"- {a['title']} ({a['source']})" for a in data.get("articles",[])[:5]])
    except: return "Nouvelles indisponibles"

def clean_for_tts(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = text.replace('*', '').replace('#', '').replace('_', ' ')
    text = re.sub(r'(\d+):(\d+)-(\d+)', r'\1 verset \2 a \3', text)
    text = re.sub(r'(\d+):(\d+)', r'\1 verset \2', text)
    return text

def tts(text, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    gTTS(text=clean_for_tts(text), lang='fr', slow=False).save(out_path)
    return Path(out_path).stat().st_size // 1024

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key",    required=True)
    parser.add_argument("--eleven-key", required=False, default=None)
    args = parser.parse_args()

    client = anthropic.Anthropic(api_key=args.api_key)
    print(f"\n[RSDV] Generation resumes audio -- {TODAY}\n")

    for cat in CATEGORIES:
        out_json = Path(f"content/resumes/{cat['key']}_{TODAY}.json")
        out_mp3  = Path(f"audio/resumes/{cat['key']}_{TODAY}.mp3")

        if out_json.exists() and out_mp3.exists() and out_mp3.stat().st_size > 1000:
            print(f"[SKIP] {cat['key']}: deja genere")
            continue

        print(f"[GEN] {cat['key']}...")
        articles = get_articles(cat['key'])

        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001", max_tokens=600,
                system=cat['system'],
                messages=[{"role":"user","content":f"""Ecris un resume radio ATTRACTIF {cat['desc']}. 100-120 mots (1 min).
Articles:
{articles}
Commence par phrase accrocheuse, 2-3 nouvelles, termine positivement.
JSON: {{"title":"titre court","date":"{TODAY}","category":"{cat['key']}","resume":"texte"}}"""}]
            )
            raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
            start = raw.find("{")
            d, _ = json.JSONDecoder().raw_decode(raw[start:])
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            kb = tts(f"{d['title']}.\n\n{d['resume']}", str(out_mp3))
            print(f"[OK] {d['title']} -- {kb} KB")
        except Exception as e:
            print(f"[ERR] {cat['key']}: {e}")

    print(f"\n[DONE] Resumes termines pour {TODAY}")

if __name__ == "__main__":
    main()
