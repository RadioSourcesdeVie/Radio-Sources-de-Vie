#!/usr/bin/env python3
"""
generate_daily_audio.py — Genere les audios manquants chaque jour
Priere Matin, Priere Soir, Temoignage, Sermon, Meteo
Voix: gTTS (Google, gratuit, sans cle API)
"""
import json, argparse, re
from datetime import datetime
from pathlib import Path
from gtts import gTTS

TODAY = datetime.now().strftime("%Y-%m-%d")

def clean_for_tts(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = text.replace('*', '').replace('#', '').replace('_', ' ')
    text = re.sub(r'(\d+):(\d+)-(\d+)', r'\1 verset \2 a \3', text)
    text = re.sub(r'(\d+):(\d+)', r'\1 verset \2', text)
    return text

def tts(text, out_path):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    gTTS(text=clean_for_tts(text), lang='fr', slow=False).save(out_path)
    return Path(out_path).stat().st_size // 1024

def build_text(data):
    parts = []
    if data.get("title"):   parts.append(data["title"] + ".")
    if data.get("verse"):   parts.append(data["verse"])
    if data.get("content"): parts.append(data["content"])
    elif data.get("nugget"): parts.append(data["nugget"])
    elif data.get("text"):  parts.append(data["text"])
    return "\n\n".join(parts)

ITEMS = [
    (f"content/prayers/matin_{TODAY}.json",  f"audio/prayers/matin_{TODAY}.mp3",  "Priere Matin"),
    (f"content/prayers/soir_{TODAY}.json",   f"audio/prayers/soir_{TODAY}.mp3",   "Priere Soir"),
    (f"content/testimonies/{TODAY}.json",     f"audio/testimonies/{TODAY}.mp3",    "Temoignage"),
    (f"content/sermons/{TODAY}.json",         f"audio/sermons/{TODAY}.mp3",        "Sermon"),
    (f"content/meteo/{TODAY}.json",           f"audio/meteo/{TODAY}.mp3",          "Meteo"),
]

def generate_meteo_audio():
    json_path = f"content/meteo/{TODAY}.json"
    mp3_path  = f"audio/meteo/{TODAY}.mp3"
    if Path(mp3_path).exists() and Path(mp3_path).stat().st_size > 1000:
        print(f"[SKIP] Meteo: deja generee")
        return
    if not Path("weather.json").exists():
        print(f"[WARN] weather.json manquant")
        return
    if not Path(json_path).exists():
        data = json.loads(Path("weather.json").read_text(encoding="utf-8"))
        ottawa = data.get("ottawa", {})
        pap    = data.get("pap", {})
        mois = ["","janvier","fevrier","mars","avril","mai","juin","juillet","aout","septembre","octobre","novembre","decembre"]
        n = datetime.now()
        date_fr = f"{n.day} {mois[n.month]} {n.year}"
        text = (f"Bonjour chers auditeurs, voici la meteo du {date_fr} sur Radio Sources de Vie. "
                f"A Ottawa: {round(ottawa.get('temp',0))} degres Celsius. {ottawa.get('description','')}. "
                f"A Port-au-Prince: {round(pap.get('temp',0))} degres Celsius. {pap.get('description','')}. "
                f"Que Dieu benisse votre journee!")
        meteo = {"date": TODAY, "title": f"Meteo du {date_fr}", "ottawa": ottawa, "pap": pap, "text": text}
        Path(json_path).parent.mkdir(parents=True, exist_ok=True)
        Path(json_path).write_text(json.dumps(meteo, ensure_ascii=False, indent=2), encoding="utf-8")
    data2 = json.loads(Path(json_path).read_text(encoding="utf-8"))
    text2 = data2.get("text", "")
    if text2:
        print(f"[GEN] Meteo...")
        kb = tts(text2, mp3_path)
        print(f"[OK]  Meteo -> {kb} KB")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--eleven-key", required=False, default=None)
    args = parser.parse_args()

    print(f"\n[RSDV] Generation audios quotidiens (gTTS) -- {TODAY}\n")
    generate_meteo_audio()

    total = 0
    for json_path, mp3_path, label in ITEMS:
        if Path(mp3_path).exists() and Path(mp3_path).stat().st_size > 1000:
            print(f"[SKIP] {label}: deja genere")
            total += 1
            continue
        if not Path(json_path).exists():
            print(f"[WARN] {label}: JSON manquant -- {json_path}")
            continue
        try:
            data = json.loads(Path(json_path).read_text(encoding="utf-8"))
            text = build_text(data)
            print(f"[GEN] {label}...")
            kb = tts(text, mp3_path)
            print(f"[OK]  {label} -> {kb} KB")
            total += 1
        except Exception as e:
            print(f"[ERR] {label}: {e}")

    print(f"\n[DONE] {total}/5 audios generes")

if __name__ == "__main__":
    main()
