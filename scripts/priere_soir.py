# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Prière du soir (21:00)
Génère une longue prière du soir (15+ minutes) avec Gemini (voix Aoede).
Prière de paix, d'action de grâces et de protection pour la nuit.
Sortie : priere/priere_soir_AAAAMMJJ_HHMMSS.wav
Usage  : python priere_soir.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from utils import (
    BASE_DIR, get_timestamp, generate_text, text_to_speech,
    save_audio, save_script, get_topic_index, build_full_script
)

SUJETS = [
    "Prière du soir pour la paix de Haïti",
    "Prière du soir pour la famille et le foyer",
    "Prière du soir de protection pour la nuit",
    "Prière du soir de reconnaissance pour la journée",
    "Prière du soir pour la guérison du corps et de l'âme",
    "Prière du soir pour la diaspora haïtienne",
    "Prière du soir pour les malades et les souffrants",
    "Prière du soir de pardon et de réconciliation",
    "Prière du soir pour les gouvernants",
    "Prière du soir de provision et d'espérance",
]

OUTPUT_DIR = BASE_DIR / "priere"
OUTPUT_DIR.mkdir(exist_ok=True)


def section_ouverture_et_action_de_grace(sujet: str) -> str:
    prompt = f"""Tu es un pasteur animateur de "Radio Sources de Vie", radio chrétienne francophone.

Tu commences une longue prière radiophonique DU SOIR sur le thème : {sujet}

Génère l'OUVERTURE PAISIBLE ET L'ACTION DE GRÂCES.

INSTRUCTIONS STRICTES :
- TOUT en français — zéro anglais, zéro créole
- Commencer EXACTEMENT par : "Bienvenue à notre moment de prière du soir sur Radio Sources de Vie. En cette fin de journée, recueillons-nous ensemble devant notre Père céleste pour Lui confier tout ce que nous avons vécu."
- Minimum 600 mots
- Ton paisible, posé, profondément pastoral — ambiance du soir
- Salutation chaleureuse aux frères et sœurs en Haïti et dans la diaspora
- Action de grâces sincère pour la journée écoulée : le souffle, la santé, la famille, le travail, la provision
- Adoration paisible : qui est Dieu dans la nuit qui vient (Psaume 121, Psaume 4:8)
- Citer plusieurs versets de reconnaissance (Psaumes)
- Texte parlé fluide, pas de titres, pas de numérotation
- NE PAS conclure — d'autres sections suivent

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def section_pardon(sujet: str) -> str:
    prompt = f"""Tu es un pasteur de "Radio Sources de Vie".

Tu poursuis la prière du soir sur le thème : {sujet}

Génère la SECTION DE CONFESSION ET DE PARDON (suite directe).

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 500 mots
- Transition : "Père céleste, en ce soir, nous venons aussi devant Toi avec un cœur humble..."
- Confession sincère des manquements de la journée (paroles, pensées, actions, omissions)
- Demande de pardon
- Pardon donné aux autres (pour ne pas s'endormir avec rancœur)
- Réconciliation
- Versets bibliques de pardon (1 Jean 1:9, Matthieu 6:14-15, Éphésiens 4:26)
- Ton humble, pastoral, plein d'espérance
- Texte parlé fluide
- NE PAS conclure la prière

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def section_intercession_et_supplication(sujet: str) -> str:
    prompt = f"""Tu es un pasteur de "Radio Sources de Vie".

Tu continues la prière du soir sur le thème : {sujet}

Génère la SECTION INTERCESSION ET SUPPLICATIONS (suite directe).

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 600 mots
- Transition : "Seigneur, nous Te confions maintenant nos frères et sœurs..."
- Intercession pour Haïti : la paix, la sécurité, les enfants qui dorment, les familles
- Intercession pour la diaspora (Canada, États-Unis, France, Brésil, Chili)
- Intercession pour les malades, les hospitalisés, les agonisants
- Intercession pour ceux qui veillent : médecins, infirmiers, policiers, pompiers, pasteurs en service
- Intercession pour les enfants seuls, les sans-abris, les déprimés
- Supplications spécifiques liées au thème {sujet}
- Versets de réconfort (Psaume 4:8, Psaume 121, Matthieu 11:28)
- Ton compatissant, fervent, plein de foi
- Texte parlé fluide
- NE PAS conclure — une dernière section suit

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def section_protection_et_cloture(sujet: str) -> str:
    prompt = f"""Tu es un pasteur de "Radio Sources de Vie".

Tu termines la prière du soir sur le thème : {sujet}

Génère la SECTION FINALE : PROTECTION POUR LA NUIT ET CLÔTURE.

INSTRUCTIONS STRICTES :
- TOUT en français
- Minimum 500 mots
- Transition : "Père céleste, avant de Te dire bonne nuit..."
- Prière de protection pour la nuit (corps, esprit, foyer, voyageurs nocturnes)
- Demande d'anges veillant autour des maisons (Psaume 91:11)
- Demande de sommeil paisible et restaurateur (Psaume 4:8)
- Bénédiction sacerdotale (Nombres 6:24-26) prononcée en entier
- Une dernière action de grâces
- Inviter les auditeurs à dire "Amen" en confiance avant de dormir
- Conclure par : "Bonne nuit à tous nos auditeurs, en Haïti et dans la diaspora. Que Dieu vous garde et vous bénisse. Au revoir, sur Radio Sources de Vie."
- Ton paisible, plein de paix et de confiance
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def main():
    index = get_topic_index('priere_soir_state.json', len(SUJETS))
    sujet = SUJETS[index]

    print(f"\n=== Radio Sources de Vie — Prière du soir (21:00) ===")
    print(f"Sujet : {sujet}")
    print(f"Voix  : Gemini Aoede\n")

    print("Génération 1/4 (Ouverture et action de grâces)...")
    s1 = section_ouverture_et_action_de_grace(sujet)
    print("Génération 2/4 (Confession et pardon)...")
    s2 = section_pardon(sujet)
    print("Génération 3/4 (Intercession et supplications)...")
    s3 = section_intercession_et_supplication(sujet)
    print("Génération 4/4 (Protection pour la nuit + clôture)...")
    s4 = section_protection_et_cloture(sujet)

    texte_complet = "\n\n".join([s1, s2, s3, s4])
    mots = len(texte_complet.split())
    print(f"\nMots générés : {mots} (cible >= 2200 pour 15+ min)")

    timestamp = get_timestamp()
    titre = f"Prière du soir — {sujet}"
    full_script, tts_text = build_full_script(texte_complet, titre)

    base_nom = f"priere_soir_{timestamp}"
    txt_path = str(OUTPUT_DIR / f"{base_nom}.txt")
    wav_path = str(OUTPUT_DIR / f"{base_nom}.wav")

    save_script(full_script, txt_path)

    print("Synthèse vocale en cours (Gemini Aoede)...")
    audio = text_to_speech(tts_text)
    chemin_final = save_audio(audio, wav_path)

    print(f"\nPrière du soir générée avec succès!")
    print(f"Sujet  : {sujet}")
    print(f"Script : {txt_path}")
    print(f"Audio  : {chemin_final}")


if __name__ == '__main__':
    main()
