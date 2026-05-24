# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Prière du matin (05:00)
Génère une longue prière du matin (15+ minutes) avec Gemini (voix Aoede).
Sortie : priere/priere_matin_AAAAMMJJ_HHMMSS.wav
Usage  : python priere_matin.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    BASE_DIR, get_timestamp, generate_text, text_to_speech,
    save_audio, save_script, get_topic_index, build_full_script
)

SUJETS = [
    "Prière pour Haïti et sa délivrance",
    "Prière pour la famille et le foyer",
    "Prière de guérison du corps et de l'âme",
    "Prière de protection divine",
    "Prière de provision et bénédiction matérielle",
    "Prière de repentance sincère",
    "Prière pour la diaspora haïtienne",
    "Prière pour les gouvernants et les autorités",
    "Prière de reconnaissance et d'actions de grâces",
    "Prière pour les malades et les souffrants",
]

OUTPUT_DIR = BASE_DIR / "priere"
OUTPUT_DIR.mkdir(exist_ok=True)


def section_ouverture(sujet: str) -> str:
    prompt = f"""Tu es un pasteur animateur de "Radio Sources de Vie", radio chrétienne francophone.

Tu commences une longue prière radiophonique du matin sur le thème : {sujet}

INSTRUCTIONS STRICTES :
- TOUT en français — zéro mot anglais, zéro créole haïtien
- Commencer EXACTEMENT par : "Bienvenue à notre moment de prière du matin sur Radio Sources de Vie. En ce matin béni, nous nous tournons vers notre Père céleste pour Lui consacrer cette nouvelle journée."
- Minimum 600 mots
- Salutation chaleureuse aux frères et sœurs en Haïti et dans la diaspora
- Louange et adoration profondes : qui est Dieu, Sa fidélité, Sa grandeur, Sa beauté
- Plusieurs versets de louange (Psaumes, version Louis Segond)
- Action de grâces pour le matin, pour le souffle, pour la vie
- Ton chaleureux, pastoral, intime
- Texte parlé fluide, sans titres, sans numérotation
- NE PAS conclure la prière — c'est seulement l'ouverture, d'autres sections suivent

Génère UNIQUEMENT le texte parlé de cette section d'ouverture."""
    return generate_text(prompt)


def section_intercession(sujet: str) -> str:
    prompt = f"""Tu es un pasteur de "Radio Sources de Vie".

Tu poursuis une prière radiophonique du matin déjà commencée sur le thème : {sujet}

Génère maintenant la SECTION INTERCESSION (suite directe, sans réintroduction).

INSTRUCTIONS STRICTES :
- TOUT en français — zéro anglais, zéro créole
- Minimum 600 mots
- Transition naturelle : "Père céleste, nous Te présentons maintenant notre pays Haïti..."
- Intercession pour Haïti : enfants, familles, éducation, sécurité, économie, l'Église haïtienne
- Intercession pour la diaspora haïtienne (Canada, États-Unis, France, République dominicaine, Brésil, Chili)
- Intercession pour les gouvernants, les autorités, les leaders religieux (1 Timothée 2:1-2, Jérémie 29:7)
- Plusieurs versets bibliques d'intercession
- Adresser la prière directement à Dieu ("Père", "Seigneur", "Dieu tout-puissant")
- Ton suppliant, fervent, plein de foi
- Texte parlé fluide, sans titres ni numérotation
- NE PAS conclure la prière — d'autres sections suivent

Génère UNIQUEMENT le texte parlé de cette section."""
    return generate_text(prompt)


def section_supplications(sujet: str) -> str:
    prompt = f"""Tu es un pasteur de "Radio Sources de Vie".

Tu continues la prière du matin sur le thème : {sujet}

Génère la SECTION SUPPLICATIONS PERSONNELLES (suite directe).

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 600 mots
- Supplications spécifiques liées au thème {sujet}
- Prière pour les malades, les souffrants, les déprimés, les chômeurs, les endeuillés
- Prière pour les couples en difficulté, les jeunes, les étudiants, les enfants
- Prière pour les voyageurs, les femmes enceintes, les personnes seules
- Prière pour les pasteurs, les missionnaires, les Églises
- Versets de réconfort (Psaumes 23, Esaïe 41:10, Matthieu 11:28-30)
- Ton compatissant, pastoral, plein de foi
- Texte parlé fluide, sans titres ni numérotation
- NE PAS conclure la prière — une dernière section suit

Génère UNIQUEMENT le texte parlé de cette section."""
    return generate_text(prompt)


def section_cloture(sujet: str) -> str:
    prompt = f"""Tu es un pasteur de "Radio Sources de Vie".

Tu termines la prière radiophonique du matin sur le thème : {sujet}

Génère la SECTION DE CLÔTURE (conclusion finale).

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 500 mots
- Bénédiction sacerdotale (Nombres 6:24-26) prononcée en entier
- Encouragement à commencer la journée dans la foi et la confiance
- Promesses de Dieu pour la journée qui commence
- Une dernière prière sincère de consécration
- Doxologie finale et "Amen"
- Inviter les auditeurs à dire "Amen" avec nous
- Transition naturelle vers la conclusion ("Avant de clôturer ce moment de prière...")
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé de cette section de clôture."""
    return generate_text(prompt)


def main():
    index = get_topic_index('priere_matin_state.json', len(SUJETS))
    sujet = SUJETS[index]

    print(f"\n=== Radio Sources de Vie — Prière du matin (05:00) ===")
    print(f"Sujet : {sujet}")
    print(f"Voix  : Gemini Aoede\n")

    print("Génération 1/4 (Ouverture et louange)...")
    s1 = section_ouverture(sujet)
    print("Génération 2/4 (Intercession Haïti et diaspora)...")
    s2 = section_intercession(sujet)
    print("Génération 3/4 (Supplications personnelles)...")
    s3 = section_supplications(sujet)
    print("Génération 4/4 (Clôture et bénédiction)...")
    s4 = section_cloture(sujet)

    texte_complet = "\n\n".join([s1, s2, s3, s4])
    mots = len(texte_complet.split())
    print(f"\nMots générés : {mots} (cible >= 2200 pour 15+ min)")

    timestamp = get_timestamp()
    titre = f"Prière du matin — {sujet}"
    full_script, tts_text = build_full_script(texte_complet, titre)

    base_nom = f"priere_matin_{timestamp}"
    txt_path = str(OUTPUT_DIR / f"{base_nom}.txt")
    wav_path = str(OUTPUT_DIR / f"{base_nom}.wav")

    save_script(full_script, txt_path)

    print("Synthèse vocale en cours (Gemini Aoede)...")
    audio = text_to_speech(tts_text)
    chemin_final = save_audio(audio, wav_path)

    print(f"\nPrière du matin générée avec succès!")
    print(f"Sujet  : {sujet}")
    print(f"Script : {txt_path}")
    print(f"Audio  : {chemin_final}")


if __name__ == '__main__':
    main()
