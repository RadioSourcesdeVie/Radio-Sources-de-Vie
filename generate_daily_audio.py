#!/usr/bin/env python3
"""
generate_daily_audio.py — Génère les audios manquants chaque jour
Prière Matin, Prière Soir, Sabbat, Météo
Voix: Edge TTS (Microsoft, gratuit, sans clé API) — remplace ElevenLabs.
"""
import json, argparse, asyncio, re
from datetime import datetime
from pathlib import Path
import edge_tts

TODAY = datetime.now().strftime("%Y-%m-%d")
# Voix Edge TTS (gratuites, neurales, françaises) — équivalents des anciennes voix ElevenLabs
BELLA = "fr-CA-SylvieNeural"    # Prière / Météo — voix féminine douce (avant: Bella)
ANTONI = "fr-FR-HenriNeural"    # Sermon — voix masculine pastorale (avant: Antoni)
ELLI = "fr-FR-DeniseNeural"     # Témoignage — voix féminine naturelle (avant: Elli)

def clean_for_tts(text: str) -> str:
    """Retire le formatage markdown (**gras**, *italique*, #titres, _souligné_)
    pour que la voix ne lise pas les astérisques/symboles à voix haute."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)   # **gras**
    text = re.sub(r'\*(.*?)\*', r'\1', text)       # *italique*
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)  # _souligné_ / __gras__
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)  # # Titres
    text = text.replace('*', '').replace('#', '').replace('_', ' ')
    return text

async def _synth(text, voice, out_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(out_path)

def tts(text, voice, out_path, eleven_key=None):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synth(clean_for_tts(text), voice, out_path))
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

def generate_meteo_audio(eleven_key=None):
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
        _mois_fr = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        _n = datetime.now()
        date_fr = f"{_n.day} {_mois_fr[_n.month]} {_n.year}"
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
    parser.add_argument("--eleven-key", required=False, default=None,
                         help="Obsolète — conservé pour compatibilité, ignoré (Edge TTS ne nécessite pas de clé)")
    args = parser.parse_args()

    print(f"\n🎙️ Génération audios quotidiens (Edge TTS) — {TODAY}\n")
    generate_meteo_audio()
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
            kb = tts(text, voice, mp3_path)
            print(f"✅  {label} → {kb} KB")
            total += 1
        except Exception as e:
            print(f"❌  {label}: {e}")

    print(f"\n✅  {total}/5 audios générés")

if __name__ == "__main__":
    main()
