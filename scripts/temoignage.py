# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Segment Témoignages (18:00)
Génère un long segment de témoignages communautaires (10+ minutes) avec Gemini (voix Aoede).
Sortie : temoignage/temoignage_AAAAMMJJ_HHMMSS.wav
Usage  : python temoignage.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    BASE_DIR, get_timestamp, generate_text, text_to_speech,
    save_audio, save_script, get_topic_index, build_full_script
)

THEMES = [
    "la guérison miraculeuse et la fidélité de Dieu face à la maladie",
    "la provision divine dans une situation financière difficile",
    "le courage d'une famille haïtienne dans la diaspora qui persévère dans la foi",
    "la restauration d'un foyer brisé par la grâce de Dieu",
    "la paix surnaturelle de Dieu face à l'adversité et aux épreuves",
    "la persévérance dans la foi malgré les obstacles et les découragements",
    "la grâce de Dieu qui transforme une vie dans un moment désespéré",
    "la protection divine dans une situation dangereuse",
    "la réconciliation et le pardon dans une famille divisée",
    "l'espérance retrouvée après une période de deuil et de douleur",
    "la délivrance des chaînes du passé par la puissance de Jésus",
    "la fidélité de Dieu pour les jeunes haïtiens qui cherchent leur voie",
]

OUTPUT_DIR = BASE_DIR / "temoignage"
OUTPUT_DIR.mkdir(exist_ok=True)


def section_introduction(theme: str) -> str:
    prompt = f"""Tu es animateur chaleureux de "Radio Sources de Vie", radio chrétienne francophone.

Génère l'INTRODUCTION du segment Témoignages communautaires sur le thème : {theme}

INSTRUCTIONS STRICTES :
- TOUT en français — zéro mot anglais, zéro créole haïtien
- Commencer EXACTEMENT par : "Bienvenue à notre segment de témoignages sur Radio Sources de Vie. Ce précieux moment est dédié à tous nos auditeurs qui partagent comment Dieu a été fidèle dans leur vie."
- Minimum 350 mots
- Ton chaleureux, encourageant, pastoral, bienveillant
- Présenter le thème du jour et inviter les auditeurs à partager
- Citer un verset biblique d'encouragement à témoigner (par exemple Apocalypse 12:11 ou Psaume 107:2)
- Annoncer que plusieurs témoignages vont suivre
- Texte parlé fluide, pas de titres, pas de numérotation

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def section_temoignage_1(theme: str) -> str:
    prompt = f"""Tu es animateur de "Radio Sources de Vie".

Génère le PREMIER témoignage du segment sur le thème : {theme}

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 450 mots
- Commencer par : "Voici notre premier témoignage. Il nous vient de..."
- Inventer un témoin crédible de la communauté haïtienne avec un prénom francophone (ex. Jean-Pierre de Montréal, Marie-Luce de Port-au-Prince, Emmanuel d'Ottawa, Nathalie de Miami, Pierre-André de Gonaïves)
- Récit détaillé et émouvant : situation initiale, épreuve, intervention de Dieu, transformation, gratitude
- Inclure 1 ou 2 versets bibliques d'appui cités par le témoin
- Ton conversationnel, comme si l'animateur lisait une lettre reçue
- Encouragement bref de l'animateur en fin de témoignage
- Pas de titres, pas de numérotation visible

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def section_temoignage_2(theme: str) -> str:
    prompt = f"""Tu es animateur de "Radio Sources de Vie".

Génère le DEUXIÈME témoignage du segment sur le thème : {theme}

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 450 mots
- Commencer par une transition naturelle : "Notre deuxième témoignage nous vient de..."
- Inventer un témoin différent du premier, avec prénom francophone (Sœur Yvrose de Cap-Haïtien, Frère Wesley de Brooklyn, Sœur Carline de Pétion-Ville, etc.)
- Histoire DIFFÉRENTE du premier témoignage mais sur le même thème général
- Récit détaillé : contexte, épreuve, foi, intervention divine, témoignage actuel
- Inclure 1 ou 2 versets bibliques cités par le témoin
- Ton conversationnel, chaleureux
- Encouragement bref de l'animateur en fin
- Pas de titres ni numérotation visible

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def section_temoignage_3_et_cloture(theme: str) -> str:
    prompt = f"""Tu es animateur de "Radio Sources de Vie".

Génère le TROISIÈME et dernier témoignage du segment ET LA CLÔTURE.

Thème : {theme}

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 500 mots TOTAL (témoignage + clôture)
- Commencer par : "Et pour terminer, un dernier témoignage qui nous vient de..."
- Inventer un troisième témoin distinct avec prénom francophone
- Témoignage un peu plus bref que les deux précédents mais émouvant
- Inclure 1 verset biblique
- Après le témoignage, faire la CLÔTURE du segment :
  * Encouragement à témoigner soi-même de la bonté de Dieu
  * Invitation chaleureuse à partager son propre témoignage avec Radio Sources de Vie
  * Verset biblique de clôture (Apocalypse 12:11 ou Psaume 66:16)
  * Bénédiction finale
  * Conclure par : "Merci d'avoir partagé ce moment avec nous. Restez à l'écoute de Radio Sources de Vie."
- Pas de titres ni numérotation visible
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def main():
    index = get_topic_index('temoignage_state.json', len(THEMES))
    theme = THEMES[index]

    print(f"\n=== Radio Sources de Vie — Témoignages (18:00) ===")
    print(f"Thème : {theme}")
    print(f"Voix  : Gemini Aoede\n")

    print("Génération 1/4 (Introduction)...")
    s1 = section_introduction(theme)
    print("Génération 2/4 (Premier témoignage)...")
    s2 = section_temoignage_1(theme)
    print("Génération 3/4 (Deuxième témoignage)...")
    s3 = section_temoignage_2(theme)
    print("Génération 4/4 (Troisième témoignage + clôture)...")
    s4 = section_temoignage_3_et_cloture(theme)

    texte_complet = "\n\n".join([s1, s2, s3, s4])
    mots = len(texte_complet.split())
    print(f"\nMots générés : {mots} (cible >= 1500 pour 10+ min)")

    timestamp = get_timestamp()
    titre = f"Témoignages communautaires — {theme}"
    full_script, tts_text = build_full_script(texte_complet, titre)

    base_nom = f"temoignage_{timestamp}"
    txt_path = str(OUTPUT_DIR / f"{base_nom}.txt")
    wav_path = str(OUTPUT_DIR / f"{base_nom}.wav")

    save_script(full_script, txt_path)

    print("Synthèse vocale en cours (Gemini Aoede)...")
    audio = text_to_speech(tts_text)
    chemin_final = save_audio(audio, wav_path)

    print(f"\nSegment Témoignages généré avec succès!")
    print(f"Thème  : {theme}")
    print(f"Script : {txt_path}")
    print(f"Audio  : {chemin_final}")


if __name__ == '__main__':
    main()
