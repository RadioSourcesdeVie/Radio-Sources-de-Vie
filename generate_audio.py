#!/usr/bin/env python3
"""
generate_audio.py — Convertit prière/sermon/témoignage en MP3 via ElevenLabs
Radio Sources de Vie Chrétienne
"""
import json, sys, requests
from datetime import datetime
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")
API_KEY = "a4926ea519ea319e71e04f3f01133b379741e80824690d2d9f9319f964f851f3"

# Voix française naturelle (Rachel — multilingual)
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
MODEL_ID  = "eleven_multilingual_v2"

CONTENT_TYPES = {
    "prayer":    {"dir": "content/prayers",     "audio": "audio/prayers",     "icon": "🙏"},
    "sermon":    {"dir": "content/sermons",      "audio": "audio/sermons",     "icon": "📖"},
    "testimony": {"dir": "content/testimonies",  "audio": "audio/testimonies", "icon": "❤️"},
}

def text_to_speech(text, out_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text[:4500],  # limite sécurité
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    Path(out_path).write_bytes(r.content)
    size_kb = Path(out_path).stat().st_size // 1024
    return size_kb

def main():
    print(f"\n🎙️  Génération audio — {TODAY}\n")
    total = 0

    for ctype, cfg in CONTENT_TYPES.items():
        json_file = Path(cfg["dir"]) / f"{TODAY}.json"
        if not json_file.exists():
            print(f"⏭️  {ctype}: pas de contenu pour aujourd'hui")
            continue

        audio_dir = Path(cfg["audio"])
        audio_dir.mkdir(parents=True, exist_ok=True)
        out_file = audio_dir / f"{TODAY}.mp3"

        if out_file.exists():
            print(f"⏭️  {cfg['icon']} {ctype}: audio déjà généré")
            total += 1
            continue

        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            # Construire le texte à lire
            text = ""
            if data.get("title"):
                text += f"{data['title']}.\n\n"
            if data.get("verse"):
                text += f"{data['verse']}\n\n"
            if data.get("content"):
                text += data["content"]

            print(f"🎤  {cfg['icon']} {ctype}: génération ({len(text)} caractères)...")
            size_kb = text_to_speech(text, out_file)
            print(f"✅  {ctype} → {out_file} ({size_kb} KB)")
            total += 1

        except requests.HTTPError as e:
            print(f"❌  {ctype}: erreur API — {e.response.status_code} {e.response.text[:100]}")
        except Exception as e:
            print(f"❌  {ctype}: {e}")

    print(f"\n✅  {total}/3 fichiers audio générés")

    # Mettre à jour audio_index.json pour le site
    index = {}
    for ctype, cfg in CONTENT_TYPES.items():
        mp3 = Path(cfg["audio"]) / f"{TODAY}.mp3"
        index[ctype] = str(mp3) if mp3.exists() else None
    Path("audio_index.json").write_text(
        json.dumps({"date": TODAY, "files": index}, indent=2),
        encoding="utf-8"
    )
    print(f"📋  audio_index.json mis à jour")

if __name__ == "__main__":
    main()
