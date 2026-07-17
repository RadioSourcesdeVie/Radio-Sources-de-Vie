#!/usr/bin/env python3
"""
generate_bulletin_soir.py — Journal du Soir, 10-15 minutes (Lundi-Vendredi, 18h)
Radio Sources de Vie Chrétienne

Compile les 4 catégories de nouvelles déjà collectées dans la journée
(content/news/{chretien,haiti,monde,sport}_{TODAY}.json, via fetch_news.py)
en un seul journal parlé complet, avec citation explicite des sources.
Texte: Claude. Audio: Edge TTS (voix Charlotte / Eloise, gratuit).
"""
import anthropic, json, argparse, asyncio, re
from datetime import datetime
from pathlib import Path
import edge_tts

TODAY = datetime.now().strftime("%Y-%m-%d")
CHARLOTTE = "fr-FR-EloiseNeural"  # même voix que les résumés du jour, pour la cohérence de marque

CATEGORIES = [
    {"key": "chretien", "label": "Nouvelles chrétiennes", "icon": "✝️"},
    {"key": "haiti",    "label": "Nouvelles d'Haïti",      "icon": "🇭🇹"},
    {"key": "monde",    "label": "Nouvelles du monde",     "icon": "🌍"},
    {"key": "sport",    "label": "Sport",                  "icon": "⚽"},
]

SYSTEM = ("Tu es Charlotte, présentatrice du journal du soir de Radio Sources de Vie, "
          "une radio chrétienne francophone pour la diaspora haïtienne au Canada. "
          "Ton style: professionnel, chaleureux, clair, jamais robotique ni une liste de titres.")


def get_articles(category, limit=6):
    try:
        data = json.loads(Path(f"content/news/{category}_{TODAY}.json").read_text(encoding="utf-8"))
        arts = data.get("articles", [])[:limit]
        lines = []
        for a in arts:
            desc = (a.get("desc") or "").strip()
            lines.append(f"- {a['title']} ({a.get('source','')}) — {desc}")
        return "\n".join(lines) if lines else None
    except Exception:
        return None


def gen_section(client, cat, articles_text):
    if not articles_text:
        return f"Pas d'actualité {cat['label'].lower()} particulière à signaler aujourd'hui."
    prompt = f"""Écris la section "{cat['label']}" du journal du soir ({TODAY}) pour Radio Sources de Vie.

Voici les vraies informations disponibles aujourd'hui (titre, source, résumé) :
{articles_text}

Consignes:
- 300 à 400 mots
- Style journal radio parlé, fluide, jamais une liste de titres collés
- Mentionne explicitement 2 à 4 sources par leur nom (ex: "selon France 24...", "rapporte Morning Star News...") pour la crédibilité
- Reste fidèle aux faits donnés ci-dessus, n'invente aucun fait
- Commence par une transition naturelle vers le sujet, pas juste le nom de la catégorie tout sec
- N'utilise AUCUN symbole markdown (pas de **, pas de #, pas de _)"""
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001", max_tokens=900,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()


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


def tts(text, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synth(clean_for_tts(text), CHARLOTTE, out_path))
    return Path(out_path).stat().st_size // 1024


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, help="Clé Anthropic")
    args = parser.parse_args()
    client = anthropic.Anthropic(api_key=args.api_key)

    out_json = Path(f"content/bulletin_soir/{TODAY}.json")
    out_mp3 = Path(f"audio/bulletin_soir/{TODAY}.mp3")

    if out_json.exists() and out_mp3.exists():
        print("⏭️  Journal du soir déjà généré aujourd'hui")
        return

    print(f"\n📻 Génération du Journal du Soir — {TODAY}\n")

    now_h = datetime.now().strftime("%Hh%M")
    intro = (f"Bonsoir chers auditeurs, il est {now_h}, bienvenue au journal du soir "
             f"de Radio Sources de Vie. Voici les nouvelles de votre journée.")

    sections = []
    if not out_json.exists():
        for cat in CATEGORIES:
            print(f"  {cat['icon']} {cat['label']}...")
            articles_text = get_articles(cat['key'])
            section_text = gen_section(client, cat, articles_text)
            sections.append({"key": cat['key'], "label": cat['label'], "text": section_text})

        outro = ("Voilà qui conclut notre journal du soir. Merci de nous avoir suivi, et que "
                 "Dieu bénisse votre soirée. Nous vous retrouvons demain, à la même heure, "
                 "sur Radio Sources de Vie.")

        full_text = intro + "\n\n" + "\n\n".join(s["text"] for s in sections) + "\n\n" + outro
        words = len(full_text.split())
        minutes = round(words / 150, 1)

        data = {
            "date": TODAY, "title": f"Journal du Soir — {TODAY}",
            "intro": intro, "sections": sections, "outro": outro,
            "content": full_text, "words": words, "minutes": minutes
        }
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ Texte généré — {words} mots (~{minutes} min) → {out_json}")
    else:
        data = json.loads(out_json.read_text(encoding="utf-8"))
        print("⏭️  Texte déjà généré, passage direct à l'audio")

    if not out_mp3.exists():
        print("🎤 Synthèse vocale...")
        kb = tts(data["content"], str(out_mp3))
        print(f"✅ Audio → {out_mp3} ({kb} KB)")
    else:
        print("⏭️  Audio déjà généré")


if __name__ == "__main__":
    main()
