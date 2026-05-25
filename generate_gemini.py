#!/usr/bin/env python3
"""
generate_gemini.py — Résumés et commentaires chrétiens via Google Gemini
Radio Sources de Vie Chrétienne — Tout en français
"""
import json, sys, requests
from datetime import datetime
from pathlib import Path

TODAY    = datetime.now().strftime("%Y-%m-%d")
API_KEY  = "AIzaSyCwohhMyTUi9tM-Ry34DCqYdbrwTi-ctI8"
API_URL  = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

def gemini(prompt):
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    r = requests.post(API_URL, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

def load_news():
    try:
        data = json.loads(Path("news_latest.json").read_text(encoding="utf-8"))
        articles = []
        for cat in ["chretien", "haiti", "monde"]:
            for a in data.get(cat, [])[:3]:
                articles.append(f"[{cat.upper()}] {a['title']} — {a['desc'][:100]}")
        return "\n".join(articles)
    except:
        return ""

def generate_news_summary(news_text):
    if not news_text:
        return None
    prompt = f"""Tu es le journaliste chrétien de Radio Sources de Vie, une radio francophone pour la diaspora haïtienne à Ottawa.

Voici les nouvelles du jour ({TODAY}):
{news_text}

Écris un bulletin d'information radiophonique en français élégant (300-400 mots) qui:
1. Résume les nouvelles les plus importantes
2. Donne une perspective chrétienne bienveillante
3. Commence par "Chers auditeurs, bonsoir et bienvenue..."
4. Termine par une parole d'encouragement biblique

Écris directement le bulletin, sans introduction ni commentaire."""
    return gemini(prompt)

def generate_christian_commentary(news_text):
    if not news_text:
        return None
    prompt = f"""Tu es un pasteur chrétien évangélique francophone de Radio Sources de Vie.

Actualités du {TODAY}:
{news_text}

Écris un court commentaire chrétien en français (200-250 mots) qui:
1. Prend une actualité marquante
2. L'éclaire avec la Parole de Dieu
3. Encourage les auditeurs dans leur foi
4. Cite un verset biblique pertinent (version Louis Segond)

Format JSON uniquement:
{{"title": "titre du commentaire", "verse": "verset cité", "reference": "Livre Ch:V", "content": "le commentaire complet"}}"""
    return gemini(prompt)

def generate_translated_summary():
    prompt = f"""Tu es traducteur pour Radio Sources de Vie, radio chrétienne francophone.

Traduis et résume en français élégant les informations suivantes sur Haïti et la communauté haïtienne chrétienne d'Ottawa pour le {TODAY}.

Inclus:
- Situation générale en Haïti
- Vie de la diaspora haïtienne au Canada
- Événements chrétiens importants

Écris 150-200 mots en français, ton bienveillant et informatif."""
    return gemini(prompt)

def main():
    print(f"\n🤖 Génération Gemini — {TODAY}\n")
    out_dir = Path("content/gemini")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{TODAY}.json"

    if out_file.exists():
        print(f"⏭️  Contenu Gemini déjà généré pour aujourd'hui")
        return

    news_text = load_news()
    result = {"date": TODAY, "generated": datetime.utcnow().isoformat()+"Z"}

    # 1. Bulletin d'information
    print("📻 Génération bulletin d'information...")
    try:
        result["bulletin"] = generate_news_summary(news_text)
        print(f"✅ Bulletin: {len(result['bulletin'])} caractères")
    except Exception as e:
        print(f"❌ Bulletin: {e}")
        result["bulletin"] = None

    # 2. Commentaire chrétien
    print("✝️  Génération commentaire chrétien...")
    try:
        raw = generate_christian_commentary(news_text)
        raw = raw.replace("```json","").replace("```","").strip()
        result["commentary"] = json.loads(raw)
        print(f"✅ Commentaire: {result['commentary'].get('title','')}")
    except Exception as e:
        print(f"❌ Commentaire: {e}")
        result["commentary"] = None

    # 3. Résumé Haïti/diaspora
    print("🇭🇹 Génération résumé Haïti/diaspora...")
    try:
        result["haiti_summary"] = generate_translated_summary()
        print(f"✅ Résumé Haïti: {len(result['haiti_summary'])} caractères")
    except Exception as e:
        print(f"❌ Résumé Haïti: {e}")
        result["haiti_summary"] = None

    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Tout sauvegardé → {out_file}")

if __name__ == "__main__":
    main()
