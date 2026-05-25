#!/usr/bin/env python3
"""
generate_audio.py — TTS ElevenLabs avec voix spécialisées
Radio Sources de Vie Chrétienne
"""
import json, sys, requests
from datetime import datetime
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")
API_KEY = "a4926ea519ea319e71e04f3f01133b379741e80824690d2d9f9319f964f851f3"
MODEL_ID = "eleven_multilingual_v2"

# Voix spécialisées
VOICES = {
    "prayer":    {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella — voix féminine douce"},
    "sermon":    {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni — pasteur masculin"},
    "testimony": {"id": "MF3mGyEYCl7XYWbV9V6O", "name": "Elli — témoignage naturel"},
}

CONTENT_TYPES = {
    "prayer":    {"dir": "content/prayers",    "audio": "audio/prayers",    "icon": "🙏"},
    # sermon: audio produit manuellement par le pasteur
    "testimony": {"dir": "content/testimonies", "audio": "audio/testimonies","icon": "❤️"},
}

def get_available_voices():
    """Récupère les voix disponibles sur le compte."""
    try:
        r = requests.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": API_KEY},
            timeout=10
        )
        r.raise_for_status()
        return {v["name"]: v["voice_id"] for v in r.json().get("voices", [])}
    except Exception as e:
        print(f"⚠️  Impossible de récupérer les voix: {e}")
        return {}

def text_to_speech(text, voice_id, out_path):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text[:4500],
        "model_id": MODEL_ID,
        "voice_settings": {"stability": 0.6, "similarity_boost": 0.8}
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    Path(out_path).write_bytes(r.content)
    return Path(out_path).stat().st_size // 1024

def main():
    print(f"\n🎙️  Génération audio — {TODAY}")
    
    # Vérifier les voix disponibles
    print("\n📋 Voix disponibles sur votre compte:")
    available = get_available_voices()
    for name, vid in list(available.items())[:8]:
        print(f"   • {name}: {vid}")

    total = 0
    for ctype, cfg in CONTENT_TYPES.items():
        json_file = Path(cfg["dir"]) / f"{TODAY}.json"
        if not json_file.exists():
            print(f"\n⏭️  {cfg['icon']} {ctype}: pas de contenu")
            continue

        audio_dir = Path(cfg["audio"])
        audio_dir.mkdir(parents=True, exist_ok=True)
        out_file = audio_dir / f"{TODAY}.mp3"

        if out_file.exists():
            print(f"\n⏭️  {cfg['icon']} {ctype}: déjà généré")
            total += 1
            continue

        voice = VOICES[ctype]
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            text = ""
            if data.get("title"):  text += f"{data['title']}.\n\n"
            if data.get("verse"):  text += f"{data['verse']}\n\n"
            if data.get("content"): text += data["content"]

            print(f"\n🎤  {cfg['icon']} {ctype} ({voice['name']})...")
            print(f"    {len(text)} caractères → {out_file}")
            size_kb = text_to_speech(text, voice["id"], out_file)
            print(f"    ✅ {size_kb} KB")
            total += 1

        except requests.HTTPError as e:
            code = e.response.status_code
            msg  = e.response.text[:150]
            print(f"\n❌  {ctype}: HTTP {code} — {msg}")
            # Fallback voix universelle
            if code == 404:
                print(f"    ↩️  Fallback voix universelle...")
                try:
                    fallback_id = "21m00Tcm4TlvDq8ikWAM"
                    size_kb = text_to_speech(text, fallback_id, out_file)
                    print(f"    ✅ Fallback OK — {size_kb} KB")
                    total += 1
                except Exception as e2:
                    print(f"    ❌ Fallback échoué: {e2}")
        except Exception as e:
            print(f"\n❌  {ctype}: {e}")

    # Mettre à jour audio_index.json
    index = {}
    for ctype, cfg in CONTENT_TYPES.items():
        mp3 = Path(cfg["audio"]) / f"{TODAY}.mp3"
        index[ctype] = f"{cfg['audio']}/{TODAY}.mp3" if mp3.exists() else None

    Path("audio_index.json").write_text(
        json.dumps({"date": TODAY, "files": index}, indent=2),
        encoding="utf-8"
    )
    print(f"\n✅  {total}/3 audios générés")
    print(f"📋  audio_index.json mis à jour\n")

if __name__ == "__main__":
    main()
