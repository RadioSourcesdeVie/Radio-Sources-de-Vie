#!/usr/bin/env python3
"""
generate_sermon.py — Sermon 20min en sections multiples
Radio Sources de Vie Chrétienne — Texte + Audio (Edge TTS, voix Henri)
"""
import anthropic, json, re
from datetime import datetime, timedelta
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")
DAY_NUM = datetime.now().timetuple().tm_yday  # jour de l'année, pour faire tourner les thèmes

# Rotation de thèmes pour éviter que Claude retombe toujours sur "La puissance de la foi"
# Liste volontairement large et variée (sujets doctrinaux, vie chrétienne, figures et récits
# bibliques, paraboles) — élargie en 2026-09 à la demande de Souvenan pour plus de diversité.
SERMON_THEMES = [
    "la foi", "l'espérance", "le pardon", "la persévérance dans l'épreuve", "la prière",
    "la grâce de Dieu", "l'obéissance à Dieu", "la guérison intérieure", "la paix intérieure",
    "le service et l'humilité", "la générosité", "la famille chrétienne", "la protection divine",
    "la repentance", "la joie du salut", "la patience", "le combat spirituel", "la fidélité de Dieu",
    "la vocation et le dessein de Dieu", "la libération des chaînes du passé", "la sagesse divine",
    "l'humilité devant Dieu", "la reconnaissance", "la confiance en Dieu", "la résurrection et la vie nouvelle",
    "la nouvelle naissance", "le fruit du Saint-Esprit", "la mission de l'Église", "la crainte de Dieu",
    "la sanctification", "le pardon des offenses", "l'amour du prochain", "la persévérance de la prière",
    "la restauration après la chute", "l'identité en Christ",
    # -- thèmes ajoutés pour plus de variété --
    "le Saint-Esprit et ses dons", "l'adoration et la louange", "l'évangélisation et le témoignage",
    "l'amour de Dieu", "la souveraineté de Dieu", "les promesses de Dieu", "la vie éternelle",
    "le combat contre la peur", "le renouvellement de l'esprit", "la compassion", "l'unité dans l'Église",
    "l'attente et la patience envers Dieu", "le jeûne et la discipline spirituelle", "l'espoir en temps de crise",
    "la fidélité dans les petites choses", "le repos en Dieu", "la guérison des relations brisées",
    "la bonté de Dieu", "être lumière du monde", "être sel de la terre", "la nouvelle création en Christ",
    "le royaume de Dieu", "les béatitudes", "la solitude et la présence de Dieu", "le pardon de soi-même",
    "la réconciliation", "le doute et la foi", "la bénédiction divine", "la vie éternelle et l'au-delà",
    "les relations familiales et le foyer", "la discipline et la formation du caractère",
    # -- figures et récits bibliques --
    "la parabole du fils prodigue", "la parabole du semeur", "la parabole du bon Samaritain",
    "la foi d'Abraham", "la vie de Joseph et le pardon", "la vie de David et la repentance",
    "l'histoire d'Esther et le courage", "l'histoire de Ruth et la fidélité", "le voyage de l'apôtre Paul",
    "la croix et la rédemption", "les miracles de Jésus", "le sermon sur la montagne",
    "la vie de prière de Jésus", "l'appel des premiers disciples", "la femme au puits et la restauration",
    "Job et la souffrance", "Moïse et la libération", "Daniel et la fidélité en exil",
]

def get_recent_sermons(days=7):
    """Lit titres/références des derniers jours pour éviter les répétitions de sujet."""
    recent = []
    for i in range(1, days + 1):
        past = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        f = Path(f"content/sermons/{past}.json")
        if f.exists():
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if d.get("title"):
                    recent.append(f"{d['title']} ({d.get('reference','')})")
            except Exception:
                pass
    return recent


def clean_markdown(text: str) -> str:
    """Retire le formatage markdown que Claude ajoute parfois (##, **, _)
    pour que le texte s'affiche proprement sur le site (pas de symboles bruts)."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    return text.strip()

def generate_sermon(api_key):
    client = anthropic.Anthropic(api_key=api_key)
    out_file = Path(f"content/sermons/{TODAY}.json")
    
    if out_file.exists():
        print(f"⏭️  Sermon déjà généré pour aujourd'hui")
        return True

    print("✍️  Génération sermon 20min...")

    theme = SERMON_THEMES[DAY_NUM % len(SERMON_THEMES)]
    recent = get_recent_sermons()
    avoid = ("\n".join(f"  - {r}" for r in recent)) if recent else "  (aucun)"

    # Sujet
    sujet_msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=150,
        messages=[{"role":"user","content":f"""Donne un titre de sermon chrétien évangélique en français sur le thème « {theme} » et un verset (Louis Segond) qui s'y rapporte.
NE RÉPÈTE PAS ces titres/versets déjà utilisés récemment:
{avoid}
Format exact: TITRE|VERSET|REFERENCE"""}]
    )
    parts = sujet_msg.content[0].text.strip().split("|")
    titre     = parts[0].strip() if len(parts)>0 else "Sermon du jour"
    verset    = parts[1].strip() if len(parts)>1 else ""
    reference = parts[2].strip() if len(parts)>2 else ""
    print(f"   Sujet: {titre}")

    SYSTEM = ("Tu es un pasteur chrétien évangélique francophone. Tu prêches avec profondeur biblique, "
              "exemples concrets et chaleur pastorale pour la diaspora haïtienne au Canada. "
              "IMPORTANT: ne mentionne jamais un jour précis de la semaine (dimanche, samedi, lundi, etc.) "
              "car ce sermon peut être écouté n'importe quel jour — tu peux parler de l'église, du culte, "
              "de la communauté des croyants, mais jamais d'un jour de la semaine spécifique. Si tu as besoin "
              "d'évoquer un cycle ou un rythme, dis « les sept jours » plutôt que de nommer un jour précis. "
              "IMPORTANT: ne mentionne jamais que la station ou l'Église est « adventiste », « adventiste du "
              "septième jour » ou toute autre étiquette dénominationnelle précise — reste toujours sur un "
              "langage chrétien général (l'Église, les croyants, le peuple de Dieu). "
              "IMPORTANT: varie tes illustrations — ne retombe pas systématiquement sur l'histoire d'une "
              "personne venue d'Haïti pour travailler à Montréal. Puise plutôt dans des scènes de vie variées: "
              "la vie de famille, le travail, la santé, l'amitié, l'attente, le deuil, la joie, des paraboles "
              "bibliques, ou des scènes de la vie quotidienne en général — sans répéter toujours le même type "
              "d'histoire d'un sermon à l'autre.")

    sections_prompts = [
        f"Écris l'INTRODUCTION de ce sermon (300 mots minimum): '{titre}'. Commence par une histoire vraie accrocheuse (varie le type d'histoire, pas toujours une histoire de migration/travail), présente le sujet et le verset: {verset}. Termine l'introduction par une question qui engage l'auditeur.",
        f"Écris le POINT 1 de ce sermon (500 mots minimum): '{titre}'. Premier enseignement majeur avec 2-3 exemples bibliques concrets et une illustration de vie réelle et actuelle (varie le type de situation — famille, travail, santé, relations, épreuve — sans répéter toujours le même scénario de migration).",
        f"Écris le POINT 2 de ce sermon (500 mots minimum): '{titre}'. Deuxième enseignement avec versets d'appui multiples, illustrations pratiques variées et application pour aujourd'hui.",
        f"Écris le POINT 3 de ce sermon (500 mots minimum): '{titre}'. Troisième enseignement avec application concrète, défis pratiques pour la semaine et encouragements.",
        f"Écris la CONCLUSION de ce sermon (400 mots minimum): '{titre}'. Histoire illustrative émouvante (variée, pas un scénario répétitif), résumé des 3 points, appel à l'action concret et prière finale.",
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

    texte_complet = clean_markdown(texte_complet)

    mots_interdits = ("dimanche", "samedi", "lundi", "mardi", "mercredi", "jeudi", "vendredi",
                       "adventiste", "septième jour")
    for mot in mots_interdits:
        if mot in texte_complet.lower():
            print(f"⚠️  Le mot '{mot}' est apparu dans le sermon malgré la consigne — vérifier le texte")

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
