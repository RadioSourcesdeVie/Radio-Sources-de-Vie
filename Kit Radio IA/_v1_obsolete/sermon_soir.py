# -*- coding: utf-8 -*-
"""
Kit Radio IA - Sermon du soir (20:00 par défaut)
Génère un long sermon (15+ minutes) avec Gemini.
Structure : Introduction, 3 points principaux, Conclusion, Appel à l'autel.
Rotation des sujets — jamais le même deux jours d'affilée (state/sermon_soir_state.json).
Sortie : sermon/sermon_soir_AAAAMMJJ_HHMMSS.wav
Usage  : python sermon_soir.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from utils import (
    BASE_DIR, get_timestamp, generate_text, text_to_speech,
    save_audio, save_script, get_topic_index, build_full_script, verifier_config
)

verifier_config()

SUJETS = [
    ("La foi qui déplace les montagnes", "Matthieu 17:20"),
    ("La grâce de Dieu suffit", "2 Corinthiens 12:9"),
    ("Cherchez premièrement le royaume de Dieu", "Matthieu 6:33"),
    ("Les promesses de Dieu sont oui et amen", "2 Corinthiens 1:20"),
    ("L'espoir au fond du désespoir", "Jérémie 29:11"),
    ("La traversée du désert — l'Éternel combattra pour vous", "Exode 14:14"),
    ("La puissance de la prière fervente", "Jacques 5:16"),
    ("La paix qui surpasse tout entendement", "Philippiens 4:7"),
    ("Dieu pourvoit à tous nos besoins", "Philippiens 4:19"),
    ("Marcher par la foi et non par la vue", "2 Corinthiens 5:7"),
]

OUTPUT_DIR = BASE_DIR / "sermon"
OUTPUT_DIR.mkdir(exist_ok=True)

_DIASPORA_LIGNE = f" et dans {config.NOM_DIASPORA}" if config.NOM_DIASPORA else ""


def section_introduction(sujet: str, verset: str) -> str:
    prompt = f"""Tu es un pasteur animateur de "{config.STATION_NOM}", radio chrétienne francophone.

Tu commences un long sermon radiophonique DU SOIR sur le thème : "{sujet}"
Verset principal : {verset}

Génère l'INTRODUCTION du sermon.

INSTRUCTIONS STRICTES :
- TOUT en {config.STATION_LANGUE}
- Commencer EXACTEMENT par : "Chers auditeurs de {config.STATION_NOM}, bienvenue à ce moment de la Parole de Dieu. Que la grâce et la paix de notre Seigneur Jésus-Christ soient avec vous en cette soirée."
- Minimum 500 mots
- Salutation chaleureuse aux frères et sœurs{_DIASPORA_LIGNE}
- Présenter le thème du jour et le contexte du verset principal
- Lire le verset {verset} en français (Louis Segond)
- Donner le contexte biblique du verset (livre, auteur, situation historique)
- Préparer le terrain pour les trois points qui vont suivre
- Ton pastoral, chaleureux, engageant
- Texte parlé fluide, pas de titres, pas de numérotation
- NE PAS développer les points — c'est juste l'introduction

Génère UNIQUEMENT le texte parlé de l'introduction."""
    return generate_text(prompt)


def section_point(sujet: str, verset: str, numero: int, focus: str) -> str:
    introductions = {
        1: "Premièrement, mes bien-aimés, considérons que...",
        2: "Passons maintenant à notre deuxième pensée. Frères et sœurs, voyez que...",
        3: "Enfin, et c'est notre troisième pensée, retenons que..."
    }
    transition = introductions[numero]

    prompt = f"""Tu es un pasteur prêchant un sermon radiophonique du SOIR sur "{config.STATION_NOM}".

Thème : "{sujet}" (verset principal : {verset})
Génère le POINT {numero} sur 3 : {focus}

INSTRUCTIONS STRICTES :
- TOUT en {config.STATION_LANGUE}
- Minimum 550 mots
- Commencer par une transition naturelle proche de : "{transition}"
- Développer ce point avec profondeur
- Citer 2 ou 3 versets bibliques d'appui (Louis Segond)
- Donner une illustration concrète (exemple de vie, situation que vit la communauté)
- Application pratique pour la vie quotidienne
- Ton pastoral, profond, engageant, encourageant
- Texte parlé fluide, pas de titres, pas de numérotation visible dans le texte
- NE PAS conclure le sermon — d'autres points suivent

Génère UNIQUEMENT le texte parlé de ce point."""
    return generate_text(prompt)


def section_conclusion_et_appel(sujet: str, verset: str) -> str:
    prompt = f"""Tu es un pasteur terminant un sermon radiophonique DU SOIR sur "{config.STATION_NOM}".

Thème : "{sujet}" (verset principal : {verset})

Génère la CONCLUSION et l'APPEL À L'AUTEL.

INSTRUCTIONS STRICTES :
- TOUT en {config.STATION_LANGUE}
- Minimum 600 mots
- Transition naturelle : "Mes bien-aimés, en concluant ce message..."
- Résumer brièvement les trois points développés
- Réaffirmer la promesse du verset {verset}
- APPEL À L'AUTEL chaleureux et sincère :
  * Inviter ceux qui ne connaissent pas encore Jésus à recevoir le salut
  * Inviter ceux qui se sont éloignés à revenir au Seigneur ce soir
  * Inviter ceux qui souffrent à confier leur fardeau au Christ avant la nuit
  * Conduire une prière de salut simple et sincère
- Bénédiction finale
- Encouragement pour la journée
- Conclure par : "Que la grâce du Seigneur Jésus soit avec vous. Restez à l'écoute de {config.STATION_NOM}."
- Ton pastoral, chaleureux, plein de foi et d'espérance
- Texte parlé fluide

Génère UNIQUEMENT le texte parlé."""
    return generate_text(prompt)


def main():
    index = get_topic_index('sermon_soir_state.json', len(SUJETS))
    sujet, verset = SUJETS[index]

    focus_points = [
        f"Comprendre la promesse divine au cœur de {sujet} — fondement biblique",
        f"Vivre concrètement {sujet} dans nos épreuves quotidiennes",
        f"Persévérer dans {sujet} — espérance et fruits dans la durée",
    ]

    print(f"\n=== {config.STATION_NOM} — Sermon du soir ===")
    print(f"Sujet  : {sujet}")
    print(f"Verset : {verset}")
    print(f"Voix   : {config.VOICE_NAME}\n")

    print("Génération 1/5 (Introduction)...")
    s1 = section_introduction(sujet, verset)
    print("Génération 2/5 (Point 1)...")
    s2 = section_point(sujet, verset, 1, focus_points[0])
    print("Génération 3/5 (Point 2)...")
    s3 = section_point(sujet, verset, 2, focus_points[1])
    print("Génération 4/5 (Point 3)...")
    s4 = section_point(sujet, verset, 3, focus_points[2])
    print("Génération 5/5 (Conclusion + appel à l'autel)...")
    s5 = section_conclusion_et_appel(sujet, verset)

    texte_complet = "\n\n".join([s1, s2, s3, s4, s5])
    mots = len(texte_complet.split())
    print(f"\nMots générés : {mots} (cible >= 2200 pour 15+ min)")

    timestamp = get_timestamp()
    titre = f"Sermon du soir — {sujet} ({verset})"
    full_script, tts_text = build_full_script(texte_complet, titre)

    base_nom = f"sermon_soir_{timestamp}"
    txt_path = str(OUTPUT_DIR / f"{base_nom}.txt")
    wav_path = str(OUTPUT_DIR / f"{base_nom}.wav")

    save_script(full_script, txt_path)

    print("Synthèse vocale en cours...")
    audio = text_to_speech(tts_text)
    chemin_final = save_audio(audio, wav_path)

    print(f"\nSermon du soir généré avec succès!")
    print(f"Sujet  : {sujet}")
    print(f"Verset : {verset}")
    print(f"Script : {txt_path}")
    print(f"Audio  : {chemin_final}")


if __name__ == '__main__':
    main()
