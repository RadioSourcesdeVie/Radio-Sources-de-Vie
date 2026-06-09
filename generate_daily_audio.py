#!/usr/bin/env python3
"""
generate_daily_audio.py — Génère les audios manquants chaque jour
Prière Matin, Prière Soir, Sabbat, Météo
"""
import requests, json, argparse
from datetime import datetime
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")
MODEL = "eleven_multilingual_v2"
BELLA = "EXAVITQu4vr4xnSDxMaL"
ANTONI = "ErXwobaYiN019PkySvjV"
ELLI = "MF3mGyEYCl7XYWbV9V6O"

def tts(text, voice, out_path, eleven_key):
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
        headers={"xi-api-key": eleven_key, "Content-Type": "application/json"},
        json={"text": text[:4500], "model_id": MODEL,
              "voice_settings": {"stability":0.65,"similarity_boost":0.8}},
        timeout=60)
    r.raise_for_status()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(r.content)
    return Path(out_path).stat().st_size // 1024

def build_text(data):
    parts = []
    if data.get("title"):  parts.append(data["title"] + ".")
    if data.get("verse"):  parts.append(data["verse"])
    if data.get("content"): parts.append(data["content"])
    elif data.get("nugget"): parts.append(data["nugget"])
    elif data.get("text"):  parts.append(data["text"])
    return "\n\n".join(parts)

ITEMS = [
    (f"content/prayers/matin_{TODAY}.json",  f"audio/prayers/matin_{TODAY}.mp3",  BELLA,  "Prière Matin"),
    (f"content/prayers/soir_{TODAY}.json",   f"audio/prayers/soir_{TODAY}.mp3",   BELLA,  "Prière Soir"),
    (f"content/testimonies/{TODAY}.json",     f"audio/testimonies/{TODAY}.mp3",     ELLI,   "Témoignage"),
    (f"content/sermons/{TODAY}.json",         f"audio/sermons/{TODAY}.mp3",         ANTONI, "Sermon"),
    (f"content/meteo/{TODAY}.json",           f"audio/meteo/{TODAY}.mp3",           BELLA,  "Météo"),
]

def generate_meteo_audio(eleven_key):
    import subprocess
    TODAY = datetime.now().strftime("%Y-%m-%d")
    json_path = f"content/meteo/{TODAY}.json"
    mp3_path = f"audio/meteo/{TODAY}.mp3"
    if Path(mp3_path).exists():
        print(f"⏭️  Météo: déjà générée")
        return
    # Générer weather.json d'abord si nécessaire
    if not Path("weather.json").exists():
        print("⚠️  weather.json manquant")
        return
    import json as json_module
    from pathlib import Path as P
    if not P(json_path).exists():
        data = json_module.loads(P("weather.json").read_text(encoding="utf-8"))
        ottawa = data.get("ottawa", {})
        pap = data.get("pap", {})
        date_fr = datetime.now().strftime("%d %B %Y")
        text = f"Bonjour chers auditeurs, voici la météo du {date_fr} sur Radio Sources de Vie. À Ottawa: {round(ottawa.get('temp',0))} degrés Celsius. {ottawa.get('description','')}. À Port-au-Prince: {round(pap.get('temp',0))} degrés Celsius. {pap.get('description','')}. Que Dieu bénisse votre journée!"
        meteo = {"date": TODAY, "title": f"Météo du {date_fr}", "ottawa": ottawa, "pap": pap, "text": text}
        P(json_path).parent.mkdir(parents=True, exist_ok=True)
        P(json_path).write_text(json_module.dumps(meteo, ensure_ascii=False, indent=2), encoding="utf-8")
    data2 = json_module.loads(P(json_path).read_text(encoding="utf-8"))
    text2 = data2.get("text","")
    if text2:
        print(f"🎤  Météo...")
        kb = tts(text2, BELLA, mp3_path, eleven_key)
        print(f"✅  Météo → {kb} KB")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eleven-key", required=True)
    args = parser.parse_args()

    print(f"\n🎙️ Génération audios quotidiens — {TODAY}\n")
    generate_meteo_audio(args.eleven_key)
    total = 0
    for json_path, mp3_path, voice, label in ITEMS:
        if Path(mp3_path).exists():
            print(f"⏭️  {label}: déjà généré")
            total += 1
            continue
        if not Path(json_path).exists():
            print(f"⚠️  {label}: JSON manquant — {json_path}")
            continue
        try:
            data = json.loads(Path(json_path).read_text(encoding="utf-8"))
            text = build_text(data)
            print(f"🎤  {label}...")
            kb = tts(text, voice, mp3_path, args.eleven_key)
            print(f"✅  {label} → {kb} KB")
            total += 1
        except Exception as e:
            print(f"❌  {label}: {e}")

    print(f"\n✅  {total}/5 audios générés")

if __name__ == "__main__":
    main()
