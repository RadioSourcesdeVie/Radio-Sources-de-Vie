#!/usr/bin/env python3
"""
generate_resumes.py — Résumés audio Charlotte pour chaque catégorie
Radio Sources de Vie Chrétienne
Voix: Edge TTS (Microsoft, gratuit, sans clé API) — remplace ElevenLabs.
"""
import anthropic, json, argparse, asyncio, re
from datetime import datetime
from pathlib import Path
import edge_tts

TODAY = datetime.now().strftime("%Y-%m-%d")

VOICE_A = "fr-BE-CharlineNeural"  # Charline — Chrétien, Haïti
VOICE_B = "fr-CA-AntoineNeural"   # Antoine — Monde, Sport

CATEGORIES = [
    {"key":"chretien","icon":"✝️","desc":"pour la communauté chrétienne mondiale","system":"Tu es Charline, présentatrice radio chrétienne francophone chaleureuse.","voice":VOICE_A},
    {"key":"haiti",   "icon":"🇭🇹","desc":"pour la diaspora haïtienne à Ottawa","system":"Tu es Charline, présentatrice radio francophone pour la diaspora haïtienne.","voice":VOICE_A},
    {"key":"monde",   "icon":"🌍","desc":"pour nos auditeurs francophones","system":"Tu es Antoine, présentateur radio francophone international.","voice":VOICE_B},
    {"key":"sport",   "icon":"⚽","desc":"sportives du jour","system":"Tu es Antoine, présentateur radio sport francophone dynamique et enthousiaste.","voice":VOICE_B},
]

def get_articles(category):
    try:
        data = json.loads(Path(f"content/news/{category}_{TODAY}.json").read_text(encoding="utf-8"))
        return "\n".join([f"- {a['title']} ({a['source']})" for a in data.get("articles",[])[:5]])
    except: return "Nouvelles indisponibles"

def clean_for_tts(text: str) -> str:
    """Retire le formatage markdown pour que la voix ne lise pas les astérisques."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = text.replace('*', '').replace('#', '').replace('_', ' ')
    return text

async def _synth(text, voice, out_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)

def tts(text, voice, out_path, eleven_key=None):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synth(clean_for_tts(text), voice, out_path))
    return Path(out_path).stat().st_size // 1024

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key",    required=True, help="Clé Anthropic")
    parser.add_argument("--eleven-key", required=False, default=None,
                         help="Obsolète — conservé pour compatibilité, ignoré (Edge TTS ne nécessite pas de clé)")
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
                model="claude-haiku-4-5-20251001", max_tokens=600,
                system=cat['system'],
                messages=[{"role":"user","content":f"""Écris un résumé radio ATTRACTIF {cat['desc']}. Longueur selon les nouvelles disponibles: si peu de nouvelles importantes 60-80 mots (45 sec), si nouvelles normales 100-120 mots (1 min), si beaucoup de nouvelles importantes 150-180 mots (1 min 30). Adapte la longueur selon l'importance et la quantité des nouvelles.
Articles:
{articles}
Commence par phrase accrocheuse, 2-3 nouvelles, termine positivement.
JSON: {{"title":"titre court attractif","date":"{TODAY}","category":"{cat['key']}","resume":"texte 60-80 mots"}}"""}]
            )
            raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
            # Claude ajoute parfois du texte après le JSON ("Extra data") — on ne parse
            # que le premier objet JSON valide et on ignore ce qui suit.
            start = raw.find("{")
            d, _ = json.JSONDecoder().raw_decode(raw[start:])
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
            kb = tts(f"{d['title']}.\n\n{d['resume']}", cat['voice'], str(out_mp3), args.eleven_key)
            print(f"✅ {d['title']} — {kb} KB")
        except Exception as e:
            print(f"❌ {cat['key']}: {e}")

    print(f"\n✅ Résumés terminés pour {TODAY}")

if __name__ == "__main__":
    main()
