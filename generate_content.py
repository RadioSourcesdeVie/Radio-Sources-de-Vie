#!/usr/bin/env python3
"""
generate_content.py — Génère prière, sermon, témoignage
Usage: python generate_content.py --api-key VOTRE_CLE_ANTHROPIC --type all
"""
import json, sys, argparse, random
from datetime import datetime, timedelta
from pathlib import Path
try:
    import anthropic
except ImportError:
    sys.exit("pip install anthropic")

TODAY = datetime.now().strftime("%Y-%m-%d")
DAY_NAME = datetime.now().strftime("%A")
DAY_NUM = datetime.now().day

# Livres bibliques par jour pour forcer la diversité
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
    "la guérison après une maladie grave",
    "retrouver la foi après un deuil",
    "sortir de la dépression par la prière",
    "la conversion d'un ancien athée",
    "Dieu pourvoie dans la pauvreté",
    "le pardon après une trahison",
    "la délivrance d'une addiction",
    "un miracle financier inattendu",
    "la réconciliation familiale",
    "trouver la paix dans l'immigration",
    "la protection divine dans un accident",
    "surmonter le rejet et l'abandon",
    "la joie retrouvée après le divorce",
    "un jeune qui trouve sa vocation",
    "la foi d'une mère célibataire",
    "la guérison d'un mariage brisé",
    "Dieu ouvre une porte professionnelle",
    "la force dans la persécution",
    "retrouver l'espoir après une fausse couche",
    "la transformation d'un ancien prisonnier",
    "vivre avec une maladie chronique par la foi",
    "la fidélité de Dieu dans la vieillesse",
    "un enfant prodigue qui revient à Dieu",
    "la provision miraculeuse de nourriture",
    "surmonter la peur par la confiance en Dieu",
    "trouver l'amour après des années de solitude",
    "la grâce de Dieu pour un pécheur repentant",
    "recevoir un visa après des années d'attente",
    "Dieu guérit les blessures de l'enfance",
    "le témoignage d'un médecin qui prie pour ses patients",
]

THEMES_PRIERE = [
    "la gratitude pour un nouveau jour",
    "la force pour affronter les défis",
    "la sagesse dans les décisions",
    "la protection de la famille",
    "la paix intérieure",
    "le courage dans l'adversité",
    "la compassion envers les autres",
    "la direction divine",
    "la guérison du corps et de l'âme",
    "la joie du salut",
    "la patience dans l'attente",
    "l'humilité devant Dieu",
    "la provision quotidienne",
    "le pardon et la réconciliation",
    "la foi pour croire l'impossible",
    "la lumière dans les ténèbres",
    "la louange et l'adoration",
    "la consécration personnelle",
    "la mission et le service",
    "l'espérance du retour de Christ",
    "la prière pour les malades",
    "la délivrance des chaînes",
    "la communion avec le Saint-Esprit",
    "la prière pour Haïti",
    "la prière pour les pasteurs",
    "la prière pour les enfants",
    "la prière pour les mariages",
    "la prière pour la diaspora",
    "la confiance dans les promesses de Dieu",
    "la prière pour la paix dans le monde",
]

def get_recent_verses(content_dir, prefix, days=5):
    """Lit les versets des jours précédents pour éviter les répétitions"""
    verses = []
    for i in range(1, days + 1):
        past = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        f = Path(content_dir) / f"{prefix}{past}.json"
        if f.exists():
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                ref = data.get("reference", "")
                title = data.get("title", "")
                if ref:
                    verses.append(f"{ref}: {title}")
            except:
                pass
    return verses

def get_books_today():
    return BOOKS_ROTATION[datetime.now().weekday()]

PROMPTS = {
    "prayer": {
        "dir": "content/prayers",
        "prefix": "matin_",
        "system": "Tu es un pasteur chrétien évangélique francophone qui s'adresse à la diaspora haïtienne au Canada. Tu connais toute la Bible par cœur et tu varies tes versets chaque jour.",
    },
    "sermon": {
        "dir": "content/sermons",
        "prefix": "",
        "system": "Tu es un prédicateur chrétien évangélique francophone avec profondeur spirituelle. Tu prêches sur des sujets variés et tu utilises des versets différents chaque jour.",
    },
    "testimony": {
        "dir": "content/testimonies",
        "prefix": "",
        "system": "Tu es un chrétien qui partage des témoignages variés et édifiants. Chaque jour un nouveau témoignage unique avec un thème complètement différent.",
    }
}

def build_prompt(content_type):
    cfg = PROMPTS[content_type]
    recent = get_recent_verses(cfg["dir"], cfg["prefix"])
    avoid = "\n".join([f"  - {v}" for v in recent]) if recent else "  (aucun)"
    books = get_books_today()
    day_seed = DAY_NUM % len(THEMES_TEMOIGNAGE)
    
    if content_type == "prayer":
        theme = THEMES_PRIERE[(DAY_NUM + datetime.now().month) % len(THEMES_PRIERE)]
        return f"""Écris une prière chrétienne du matin pour le {TODAY} sur le thème: {theme}.

RÈGLES STRICTES:
1. Choisis un verset dans ces livres UNIQUEMENT: {books}
2. NE RÉPÈTE JAMAIS ces versets déjà utilisés récemment:
{avoid}
3. Le titre doit être unique et créatif (PAS "Prière du Matin")
4. La prière doit faire 200-300 mots

Réponds UNIQUEMENT en JSON valide:
{{"title":"Titre créatif et unique","date":"{TODAY}","moment":"matin","verse":"texte complet du verset Louis Segond","reference":"Livre Ch:V","content":"prière 200-300 mots"}}"""

    elif content_type == "sermon":
        return f"""Écris un court sermon pour le {TODAY}.

RÈGLES STRICTES:
1. Choisis un verset principal dans ces livres UNIQUEMENT: {books}
2. NE RÉPÈTE JAMAIS ces versets déjà utilisés récemment:
{avoid}
3. Le titre doit être unique, inspirant et accrocheur
4. Le sermon doit avoir une intro, 3 points, et une conclusion (400-500 mots)

Réponds UNIQUEMENT en JSON valide:
{{"title":"Titre inspirant unique","date":"{TODAY}","verse":"texte complet du verset Louis Segond","reference":"Livre Ch:V","content":"sermon 400-500 mots"}}"""

    elif content_type == "testimony":
        theme = THEMES_TEMOIGNAGE[(DAY_NUM + datetime.now().month * 3) % len(THEMES_TEMOIGNAGE)]
        return f"""Écris un témoignage chrétien édifiant sur le thème: {theme}.

RÈGLES STRICTES:
1. Choisis un verset dans ces livres UNIQUEMENT: {books}
2. NE RÉPÈTE JAMAIS ces versets déjà utilisés récemment:
{avoid}
3. Le titre doit être unique et refléter le thème spécifique
4. Le témoignage doit être une histoire personnelle fictive mais réaliste (250-350 mots)
5. NE JAMAIS utiliser le titre "La fidélité de Dieu dans les épreuves"

Réponds UNIQUEMENT en JSON valide:
{{"title":"Titre unique du témoignage","date":"{TODAY}","verse":"texte complet du verset Louis Segond","reference":"Livre Ch:V","content":"témoignage 250-350 mots"}}"""

def generate(client, content_type):
    cfg = PROMPTS[content_type]
    out_dir = Path(cfg["dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if content_type == "prayer":
        out_file_matin = out_dir / f"matin_{TODAY}.json"
        out_file_soir = out_dir / f"soir_{TODAY}.json"
        if out_file_matin.exists() and out_file_soir.exists():
            print(f"⏭️  {content_type}: déjà généré aujourd'hui")
            return True
    else:
        out_file = out_dir / f"{TODAY}.json"
        if out_file.exists():
            print(f"⏭️  {content_type}: déjà généré aujourd'hui")
            return True

    print(f"✍️  Génération {content_type}...")
    try:
        prompt = build_prompt(content_type)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            system=cfg["system"],
            messages=[{"role":"user","content":prompt}]
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"): raw = raw[4:]
            raw = raw.strip()
        data = json.loads(raw)
        
        if content_type == "prayer":
            # Sauvegarder matin
            out_file_matin = out_dir / f"matin_{TODAY}.json"
            data["moment"] = "matin"
            out_file_matin.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"✅  {content_type} matin → {out_file_matin}")
            
            # Générer soir séparément
            soir_prompt = f"""Écris une prière chrétienne du soir pour le {TODAY}.

RÈGLES STRICTES:
1. Choisis un verset DIFFÉRENT de celui du matin ({data.get('reference','')})
2. Choisis dans ces livres: {get_books_today()}
3. Thème: reconnaissance pour la journée, repos en Dieu
4. 200-300 mots

Réponds UNIQUEMENT en JSON valide:
{{"title":"Titre créatif prière du soir","date":"{TODAY}","moment":"soir","verse":"texte verset Louis Segond","reference":"Livre Ch:V","content":"prière du soir 200-300 mots"}}"""
            
            msg2 = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4000,
                system=cfg["system"],
                messages=[{"role":"user","content":soir_prompt}]
            )
            raw2 = msg2.content[0].text.strip()
            if raw2.startswith("```"):
                raw2 = raw2.split("```")[1]
                if raw2.startswith("json"): raw2 = raw2[4:]
                raw2 = raw2.strip()
            data2 = json.loads(raw2)
            data2["moment"] = "soir"
            out_file_soir = out_dir / f"soir_{TODAY}.json"
            out_file_soir.write_text(json.dumps(data2, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"✅  {content_type} soir → {out_file_soir}")
        else:
            out_file = out_dir / f"{TODAY}.json"
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
    # "sermon" est exclu de "all" : le sermon long (5 sections, ~15 min) est généré
    # par generate_sermon.py, qui s'exécute juste après dans run_spirituel.sh.
    # Le laisser ici écraserait ce sermon avec une version courte (~500 mots).
    types = ["prayer","testimony"] if args.type == "all" else [args.type]
    ok = sum(generate(client, t) for t in types)
    print(f"\n🙏  {ok}/{len(types)} contenus générés pour {TODAY}")

if __name__ == "__main__":
    main()
