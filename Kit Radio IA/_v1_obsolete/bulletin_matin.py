# -*- coding: utf-8 -*-
"""
Kit Radio IA - Bulletin d'informations du matin (07:00 par défaut)
3 sections : Actualités locales / Internationales / Chrétiennes + météo.
15+ minutes de contenu. Toutes les valeurs viennent de config.py.
Sortie : nouvelles/bulletin_matin_AAAAMMJJ_HHMMSS.wav
Usage  : python bulletin_matin.py
"""
import sys
import re
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
import config
from utils import (
    BASE_DIR, get_timestamp, generate_text, text_to_speech,
    save_audio, save_script, build_full_script, verifier_config
)

verifier_config()

OUTPUT_DIR = BASE_DIR / "nouvelles"
OUTPUT_DIR.mkdir(exist_ok=True)

MOIS_FR = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre"
}
JOURS_FR = {
    0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi",
    4: "vendredi", 5: "samedi", 6: "dimanche"
}


def date_francaise() -> str:
    n = datetime.now()
    return f"{JOURS_FR[n.weekday()]} {n.day} {MOIS_FR[n.month]} {n.year}"


def nettoyer_html(texte: str) -> str:
    texte = re.sub(r'<[^>]+>', ' ', texte)
    texte = re.sub(r'&[a-zA-Z]+;', ' ', texte)
    texte = re.sub(r'\s+', ' ', texte)
    return texte.strip()


def recuperer_flux(urls: list, max_par_flux: int = 5) -> list:
    """Récupère les articles RSS d'une liste de flux."""
    articles = []
    if not urls:
        return articles
    try:
        import feedparser
    except ImportError:
        print("  AVERTISSEMENT: feedparser non installé. Exécutez: pip install feedparser")
        return articles

    for url in urls:
        try:
            print(f"  Flux: {url[:60]}...")
            flux = feedparser.parse(url)
            source_feed = flux.feed.get('title', url.split('/')[2]) if flux.feed else url.split('/')[2]
            est_google_news = 'news.google.com' in url
            for entree in flux.entries[:max_par_flux]:
                titre = nettoyer_html(entree.get('title', '')).strip()
                resume = nettoyer_html(
                    entree.get('summary', entree.get('description', ''))
                ).strip()
                source = source_feed
                if est_google_news and ' - ' in titre:
                    titre, source = titre.rsplit(' - ', 1)
                if titre and len(titre) > 5:
                    articles.append({
                        'source': source,
                        'titre': titre.strip(),
                        'resume': resume[:700] if resume else ''
                    })
        except Exception as e:
            print(f"  Erreur flux {url[:50]}: {e}")
    return articles


def recuperer_meteo(ville_api: str, ville_affichee: str) -> dict:
    try:
        url = f"https://wttr.in/{ville_api}?format=j1"
        r = requests.get(url, timeout=10,
                         headers={'User-Agent': f'{config.STATION_NOM.replace(" ", "")}/1.0'})
        d = r.json()
        a = d['current_condition'][0]
        return {
            'ville': ville_affichee,
            'temperature': a.get('temp_C', 'N/D'),
            'ressenti': a.get('FeelsLikeC', 'N/D'),
            'description': a.get('weatherDesc', [{}])[0].get('value', 'N/D'),
            'humidite': a.get('humidity', 'N/D')
        }
    except Exception as e:
        print(f"  Météo indisponible pour {ville_affichee}: {e}")
        return {
            'ville': ville_affichee, 'temperature': 'N/D', 'ressenti': 'N/D',
            'description': 'données indisponibles', 'humidite': 'N/D'
        }


def format_articles(articles: list, limite: int = 12) -> str:
    if not articles:
        return "(Aucune actualité disponible aujourd'hui depuis les flux RSS.)"
    txt = ""
    for art in articles[:limite]:
        txt += f"SOURCE: {art['source']}\nTITRE: {art['titre']}\n"
        if art['resume']:
            txt += f"RÉSUMÉ: {art['resume']}\n"
        txt += "\n"
    return txt


def texte_meteo(meteos: list) -> str:
    return "\n".join(
        f"Météo {m['ville']} : {m['temperature']}°C, ressenti {m['ressenti']}°C, "
        f"{m['description']}, humidité {m['humidite']}%"
        for m in meteos
    )


def section_intro_meteo(meteos: list) -> str:
    date_fr = date_francaise()
    prompt = f"""Tu es journaliste pour "{config.STATION_NOM}", radio chrétienne francophone.

Génère l'INTRODUCTION du bulletin d'informations du matin et la SECTION MÉTÉO.

Date du jour : {date_fr}
{texte_meteo(meteos)}

INSTRUCTIONS STRICTES :
- TOUT en {config.STATION_LANGUE} — aucune autre langue
- Minimum 400 mots
- Commencer EXACTEMENT par : "Bienvenue au bulletin d'informations du matin de {config.STATION_NOM}. Nous sommes le {date_fr}. Voici les nouvelles."
- Ton de journaliste radio professionnel, chaleureux et accessible
- Présenter la météo de façon fluide et naturelle
- Conclure la météo par une brève bénédiction sur la journée
- Annoncer brièvement ce qui suivra (actualités locales, internationales, chrétiennes)
- Pas de titres, pas de numérotation, pas de "Section 1"
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé de cette introduction."""
    return generate_text(prompt)


def section_locale(articles: list) -> str:
    prompt = f"""Tu es journaliste pour "{config.STATION_NOM}".

Génère la section ACTUALITÉS LOCALES ({config.PAYS_OU_COMMUNAUTE}) du bulletin du matin (suite directe de l'intro).

ARTICLES SOURCES :
{format_articles(articles, 10)}

INSTRUCTIONS STRICTES :
- TOUT en {config.STATION_LANGUE}
- Minimum 750 mots
- Couvrir 4 à 5 actualités locales IMPORTANTES de façon DÉTAILLÉE
- Citer les sources telles qu'elles apparaissent dans le bloc SOURCE des articles fournis (ne pas inventer)
- Transitions naturelles entre les sujets
- INTERDIT : "Histoire 1", "Histoire 2", "Article 1", toute numérotation visible
- Ton journalistique, factuel, mais empathique pour la communauté
- Commencer par une transition naturelle : "Nous commençons ce bulletin avec l'actualité locale."
- PAS de réflexion spirituelle dans cette section
- Texte parlé fluide comme un vrai journal radio
- Si aucun article n'est fourni, dis simplement qu'aucune actualité locale marquante n'est disponible aujourd'hui, sans inventer de fait.

Génère UNIQUEMENT le texte parlé de cette section."""
    return generate_text(prompt)


def section_international(articles: list) -> str:
    prompt = f"""Tu es journaliste pour "{config.STATION_NOM}".

Génère la section ACTUALITÉS INTERNATIONALES du bulletin du matin (suite directe).

ARTICLES SOURCES :
{format_articles(articles, 8)}

INSTRUCTIONS STRICTES :
- TOUT en {config.STATION_LANGUE} — traduis toute autre langue
- Minimum 550 mots
- Couvrir 2 à 3 actualités INTERNATIONALES importantes : ONU, événements mondiaux majeurs, conflits, climat, économie mondiale, diplomatie
- Détailler chaque sujet avec contexte
- Transitions naturelles entre les sujets
- INTERDIT : numérotation, "Histoire 1", "Histoire 2"
- Commencer par une transition naturelle : "Passons maintenant à l'actualité internationale."
- Ton journalistique professionnel
- PAS de réflexion spirituelle ici

Génère UNIQUEMENT le texte parlé de cette section."""
    return generate_text(prompt)


def section_chretien(articles: list) -> str:
    prompt = f"""Tu es journaliste pour "{config.STATION_NOM}".

Génère la section ACTUALITÉS CHRÉTIENNES du bulletin du matin (suite directe et finale).

ARTICLES SOURCES :
{format_articles(articles, 8)}

INSTRUCTIONS STRICTES :
- TOUT en {config.STATION_LANGUE}
- Minimum 700 mots
- Couvrir 3 à 4 actualités chrétiennes importantes : persécution, missions, croissance de l'Église, témoignages, vie de l'Église mondiale
- Citer les sources naturellement
- Transitions naturelles
- INTERDIT : numérotation, "Histoire 1", "Histoire 2"
- Commencer par une transition : "Terminons avec l'actualité chrétienne dans le monde."
- À LA FIN, ajouter UNE SEULE réflexion spirituelle brève (5 à 6 phrases maximum) commençant EXACTEMENT par : "Avant de clôturer ce bulletin, permettez-moi de partager une pensée spirituelle."
- Conclure par : "Voilà pour ce bulletin du matin sur {config.STATION_NOM}. Que Dieu vous accompagne tout au long de cette journée."
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé de cette section."""
    return generate_text(prompt)


def main():
    print(f"\n=== {config.STATION_NOM} — Bulletin du matin ===")
    print(f"Voix : {config.VOICE_NAME}\n")

    print("Récupération des flux locaux...")
    art_local = recuperer_flux(config.FLUX_LOCAL)
    print(f"  {len(art_local)} articles locaux.\n")

    print("Récupération des flux internationaux...")
    art_inter = recuperer_flux(config.FLUX_INTERNATIONAL)
    print(f"  {len(art_inter)} articles internationaux.\n")

    print("Récupération des flux chrétiens...")
    art_chr = recuperer_flux(config.FLUX_CHRETIEN)
    print(f"  {len(art_chr)} articles chrétiens.\n")

    print("Récupération météo...")
    meteos = [recuperer_meteo(config.VILLE_PRINCIPALE_API, config.VILLE_PRINCIPALE_NOM)]
    if config.VILLE_DIASPORA_NOM:
        meteos.append(recuperer_meteo(config.VILLE_DIASPORA_API, config.VILLE_DIASPORA_NOM))

    print("\nGénération 1/4 (intro + météo + bénédiction)...")
    s1 = section_intro_meteo(meteos)
    print("Génération 2/4 (actualités locales)...")
    s2 = section_locale(art_local)
    print("Génération 3/4 (actualités internationales)...")
    s3 = section_international(art_inter)
    print("Génération 4/4 (actualités chrétiennes)...")
    s4 = section_chretien(art_chr)

    texte_complet = "\n\n".join([s1, s2, s3, s4])
    mots = len(texte_complet.split())
    print(f"\nMots générés : {mots} (cible >= 2200 pour 15+ min)")

    timestamp = get_timestamp()
    titre = "Bulletin d'informations du matin"
    full_script, tts_text = build_full_script(texte_complet, titre)

    base_nom = f"bulletin_matin_{timestamp}"
    txt_path = str(OUTPUT_DIR / f"{base_nom}.txt")
    wav_path = str(OUTPUT_DIR / f"{base_nom}.wav")

    save_script(full_script, txt_path)

    print("Synthèse vocale en cours...")
    audio = text_to_speech(tts_text)
    chemin_final = save_audio(audio, wav_path)

    print(f"\nBulletin du matin généré avec succès!")
    print(f"Script : {txt_path}")
    print(f"Audio  : {chemin_final}")


if __name__ == '__main__':
    main()
