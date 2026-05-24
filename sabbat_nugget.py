#!/usr/bin/env python3
"""
Radio Sources de Vie Chrétienne
Script Sabbat School Nugget — généré chaque Samedi à 05:00
"""

import os, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

BASE_DIR = Path(r"C:\Users\avena\Desktop\radio sources De Vie")
SABBAT_DIR = BASE_DIR / "sabbat"
SABBAT_DIR.mkdir(exist_ok=True)

VOICES = {
    "sage_male": os.getenv("VOICE_SABBAT", "g5CIjZEefACoW7O5QyAGT"),
}

def generate_sabbat_text():
    """Génère le texte du Sabbat Nugget avec Claude"""
    client = Anthropic()

    # Thèmes rotatifs par semaine
    semaine = datetime.now().isocalendar()[1] % 13
    themes = [
        "La création et le repos du Sabbat",
        "La grâce de Dieu dans notre vie quotidienne",
        "La prière comme communication avec Dieu",
        "L'amour de Jésus pour les pécheurs",
        "La puissance du Saint-Esprit",
        "La fidélité de Dieu dans les épreuves",
        "Le salut par la foi en Jésus-Christ",
        "L'espérance du retour de Jésus",
        "Le service aux autres comme acte d'amour",
        "La lecture de la Bible chaque jour",
        "Le pardon et la réconciliation",
        "La famille chrétienne et ses valeurs",
        "La mission d'évangélisation"
    ]
    theme = themes[semaine]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""Génère un Sabbat School Nugget de 2 minutes (~200 mots) sur le thème: "{theme}"

Format:
- Ouverture inspirante (1-2 phrases)
- Verset biblique clé
- Leçon principale (3-4 phrases)
- Application pratique pour aujourd'hui
- Prière courte de clôture

Ton: sage, chaleureux, inspirant
Langue: Français
Public: Communauté chrétienne haïtienne"""
        }]
    )
    return response.content[0].text, theme

def generate_audio(text, filename):
    """Génère l'audio avec ElevenLabs"""
    api_key = os.getenv("ELEVENLABS_API_KEY", "")
    if not api_key:
        print("[WARN] Pas de clé ElevenLabs — audio ignoré")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICES['sage_male']}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"[OK] Audio généré: {filename}")
            return True
        else:
            print(f"[ERROR] ElevenLabs: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Audio: {e}")
        return False

def run():
    print("""
╔══════════════════════════════════════════════╗
║   SABBAT SCHOOL NUGGET — GÉNÉRATION         ║
╚══════════════════════════════════════════════╝
    """)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Générer le texte
    print("[1/3] Génération du texte...")
    text, theme = generate_sabbat_text()
    print(f"[OK] Thème: {theme}")

    # Sauvegarder le texte
    print("[2/3] Sauvegarde du texte...")
    txt_file = SABBAT_DIR / f"sabbat_nugget_{timestamp}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(f"SABBAT SCHOOL NUGGET\n")
        f.write(f"Date: {date_str}\n")
        f.write(f"Thème: {theme}\n")
        f.write("="*50 + "\n\n")
        f.write(text)
    print(f"[OK] Texte sauvegardé: {txt_file.name}")

    # Générer l'audio
    print("[3/3] Génération de l'audio...")
    wav_file = SABBAT_DIR / f"sabbat_nugget_{timestamp}.wav"
    generate_audio(text, str(wav_file))

    print(f"""
[OK] Sabbat Nugget généré!
     📄 Texte: {txt_file.name}
     🎵 Audio: {wav_file.name}
     📁 Dossier: {SABBAT_DIR}
    """)

if __name__ == "__main__":
    run()
