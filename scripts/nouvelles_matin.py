# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Bulletin d'informations du matin (07:00)
3 sections : Actualités Haïti / Internationales / Chrétiennes + météo Ottawa/Port-au-Prince.
15+ minutes de contenu.
Sortie : nouvelles/nouvelles_matin_AAAAMMJJ_HHMMSS.wav
Usage  : python nouvelles_matin.py
"""
import sys
import re
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    BASE_DIR, get_timestamp, generate_text, text_to_speech,
    save_audio, save_script, build_full_script
)

# Flux RSS Haïti VÉRIFIÉS (testés le 2026-05-10 — uniquement ceux qui renvoient des articles).
# Sources demandées non retenues : HaitiLibre (pas de RSS), AlterPresse (anti-bot),
# Le Nouvelliste (pas de RSS), RTVC (domaine inexistant).
FLUX_HAITI = [
    "https://haiti24.net/feed",
    "https://metropole.ht/feed/",
    "https://news.google.com/rss/search?q=Ha%C3%AFti&hl=fr&gl=HT&ceid=HT:fr",
]

FLUX_INTERNATIONAL = [
    "https://news.un.org/feed/subscribe/fr/news/all/rss.xml",
    "https://www.francetvinfo.fr/monde.rss",
    "https://www.rfi.fr/fr/monde/rss",
]

FLUX_CHRETIEN = [
    "https://www.info-chretienne.com/feed",
    "https://morningstarnews.org/feed",
    "https://www.porteouverte.org/feed",
    "https://www.christianpost.com/feed",
]

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
                # Google News encode la vraie source dans le titre : "Titre - Source".
                # Extraire la source réelle et nettoyer le titre.
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


def recuperer_meteo(ville_en: str, ville_fr: str) -> dict:
    try:
        url = f"https://wttr.in/{ville_en}?format=j1"
        r = requests.get(url, timeout=10,
                         headers={'User-Agent': 'RadioSourcesDeVie/3.0'})
        d = r.json()
        a = d['current_condition'][0]
        return {
            'ville': ville_fr,
            'temperature': a.get('temp_C', 'N/D'),
            'ressenti': a.get('FeelsLikeC', 'N/D'),
            'description': a.get('weatherDesc', [{}])[0].get('value', 'N/D'),
            'humidite': a.get('humidity', 'N/D')
        }
    except Exception as e:
        print(f"  Météo indisponible pour {ville_fr}: {e}")
        return {
            'ville': ville_fr, 'temperature': 'N/D', 'ressenti': 'N/D',
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


def section_intro_meteo(meteo_ott: dict, meteo_pap: dict) -> str:
    date_fr = date_francaise()
    prompt = f"""Tu es journaliste pour "Radio Sources de Vie", radio chrétienne francophone.

Génère l'INTRODUCTION du bulletin d'informations du matin et la SECTION MÉTÉO.

Date du jour : {date_fr}
Météo Ottawa, Canada : {meteo_ott['temperature']}°C, ressenti {meteo_ott['ressenti']}°C, {meteo_ott['description']}, humidité {meteo_ott['humidite']}%
Météo Port-au-Prince, Haïti : {meteo_pap['temperature']}°C, ressenti {meteo_pap['ressenti']}°C, {meteo_pap['description']}, humidité {meteo_pap['humidite']}%

INSTRUCTIONS STRICTES :
- TOUT en français — zéro anglais, zéro créole
- Minimum 400 mots
- Commencer EXACTEMENT par : "Bienvenue au bulletin d'informations du matin de Radio Sources de Vie. Nous sommes le {date_fr}. Voici les nouvelles."
- Ton de journaliste radio professionnel, chaleureux et accessible
- Présenter la météo des deux villes de façon fluide et naturelle
- Conclure la météo par une brève bénédiction sur la journée pour les frères et sœurs des deux côtés
- Annoncer brièvement ce qui suivra (actualités d'Haïti, internationales, chrétiennes)
- Pas de titres, pas de numérotation, pas de "Section 1"
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé de cette introduction."""
    return generate_text(prompt)


def section_haiti(articles: list) -> str:
    prompt = f"""Tu es journaliste pour "Radio Sources de Vie".

Génère la section ACTUALITÉS HAÏTI du bulletin du matin (suite directe de l'intro).

ARTICLES SOURCES :
{format_articles(articles, 10)}

INSTRUCTIONS STRICTES :
- TOUT en français — zéro anglais, zéro créole (traduis si nécessaire)
- Minimum 750 mots
- Couvrir 4 à 5 actualités haïtiennes IMPORTANTES de façon DÉTAILLÉE
- Citer les sources telles qu'elles apparaissent dans le bloc SOURCE des articles fournis (ne pas inventer)
- Transitions naturelles entre les sujets : "Par ailleurs...", "Dans un autre dossier...", "Sur le plan politique...", "À noter également...", "Toujours en Haïti..."
- INTERDIT : "Histoire 1", "Histoire 2", "Article 1", toute numérotation visible
- Ton journalistique, factuel, mais empathique pour la communauté haïtienne
- Commencer par une transition naturelle : "Nous commençons ce bulletin avec l'actualité d'Haïti."
- PAS de réflexion spirituelle dans cette section
- Texte parlé fluide comme un vrai journal radio

Génère UNIQUEMENT le texte parlé de cette section."""
    return generate_text(prompt)


def section_international(articles: list) -> str:
    prompt = f"""Tu es journaliste pour "Radio Sources de Vie".

Génère la section ACTUALITÉS INTERNATIONALES du bulletin du matin (suite directe).

ARTICLES SOURCES :
{format_articles(articles, 8)}

INSTRUCTIONS STRICTES :
- TOUT en français — traduis tout anglais en bon français journalistique
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
    prompt = f"""Tu es journaliste pour "Radio Sources de Vie".

Génère la section ACTUALITÉS CHRÉTIENNES du bulletin du matin (suite directe et finale).

ARTICLES SOURCES :
{format_articles(articles, 8)}

INSTRUCTIONS STRICTES :
- TOUT en français — traduis tout anglais
- Minimum 700 mots
- Couvrir 3 à 4 actualités chrétiennes importantes : persécution, missions, croissance de l'Église, témoignages, vie de l'Église mondiale
- Citer les sources naturellement (info-chretienne.com, MorningStar News, Portes Ouvertes, Christian Post)
- Transitions naturelles
- INTERDIT : numérotation, "Histoire 1", "Histoire 2"
- Commencer par une transition : "Terminons avec l'actualité chrétienne dans le monde."
- À LA FIN, ajouter UNE SEULE réflexion spirituelle brève (5 à 6 phrases maximum) commençant EXACTEMENT par : "Avant de clôturer ce bulletin, permettez-moi de partager une pensée spirituelle."
- Conclure par : "Voilà pour ce bulletin du matin sur Radio Sources de Vie. Que Dieu vous accompagne tout au long de cette journée."
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé de cette section."""
    return generate_text(prompt)


def main():
    print(f"\n=== Radio Sources de Vie — Bulletin du matin (07:00) ===")
    print(f"Voix : Gemini Aoede\n")

    print("Récupération des flux RSS Haïti...")
    art_haiti = recuperer_flux(FLUX_HAITI)
    print(f"  {len(art_haiti)} articles Haïti.\n")

    print("Récupération des flux internationaux...")
    art_inter = recuperer_flux(FLUX_INTERNATIONAL)
    print(f"  {len(art_inter)} articles internationaux.\n")

    print("Récupération des flux chrétiens...")
    art_chr = recuperer_flux(FLUX_CHRETIEN)
    print(f"  {len(art_chr)} articles chrétiens.\n")

    print("Récupération météo Ottawa et Port-au-Prince...")
    meteo_ott = recuperer_meteo('Ottawa', 'Ottawa, Canada')
    meteo_pap = recuperer_meteo('Port-au-Prince', 'Port-au-Prince, Haïti')

    print("\nGénération 1/4 (intro + météo + bénédiction)...")
    s1 = section_intro_meteo(meteo_ott, meteo_pap)
    print("Génération 2/4 (actualités Haïti)...")
    s2 = section_haiti(art_haiti)
    print("Génération 3/4 (actualités internationales)...")
    s3 = section_international(art_inter)
    print("Génération 4/4 (actualités chrétiennes + réflexion)...")
    s4 = section_chretien(art_chr)

    texte_complet = "\n\n".join([s1, s2, s3, s4])
    mots = len(texte_complet.split())
    print(f"\nMots générés : {mots} (cible >= 2200 pour 15+ min)")

    timestamp = get_timestamp()
    titre = "Bulletin d'informations du matin"
    full_script, tts_text = build_full_script(texte_complet, titre)

    base_nom = f"nouvelles_matin_{timestamp}"
    txt_path = str(OUTPUT_DIR / f"{base_nom}.txt")
    wav_path = str(OUTPUT_DIR / f"{base_nom}.wav")

    save_script(full_script, txt_path)

    print("Synthèse vocale en cours (Gemini Aoede)...")
    audio = text_to_speech(tts_text)
    chemin_final = save_audio(audio, wav_path)

    print(f"\nBulletin du matin généré avec succès!")
    print(f"Articles Haïti       : {len(art_haiti)}")
    print(f"Articles International: {len(art_inter)}")
    print(f"Articles Chrétiens   : {len(art_chr)}")
    print(f"Script : {txt_path}")
    print(f"Audio  : {chemin_final}")


if __name__ == '__main__':
    main()
