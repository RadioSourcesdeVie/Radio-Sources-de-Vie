#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Convertit en audio le contenu texte déjà généré
(prières matin/soir, témoignage, sermon, météo), avec le fournisseur de
voix choisi dans config.TTS_PROVIDER.
Usage : python generate_daily_audio.py
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config
from ai_text import verifier_config
import tts_engine

verifier_config()

TODAY = datetime.now().strftime("%Y-%m-%d")
BASE_DIR = Path(__file__).parent.parent
EXT = tts_engine.output_extension()


def build_text(data: dict) -> str:
    parts = []
    if data.get("title"):
        parts.append(data["title"] + ".")
    if data.get("verse"):
        parts.append(data["verse"])
    if data.get("content"):
        parts.append(data["content"])
    return "\n\n".join(parts)


def generate_meteo_text() -> str:
    weather_path = BASE_DIR / "weather.json"
    out_json = BASE_DIR / "content" / "meteo" / f"{TODAY}.json"
    if out_json.exists():
        return json.loads(out_json.read_text(encoding="utf-8")).get("text", "")

    if not weather_path.exists():
        print("  météo: weather.json manquant (lancez fetch_weather.py d'abord)")
        return ""

    data = json.loads(weather_path.read_text(encoding="utf-8"))
    principale = data.get("principale", {})
    diaspora = data.get("diaspora")

    _mois_fr = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
                "août", "septembre", "octobre", "novembre", "décembre"]
    n = datetime.now()
    date_fr = f"{n.day} {_mois_fr[n.month]} {n.year}"

    texte = (f"Bonjour chers auditeurs, voici la météo du {date_fr} sur {config.STATION_NOM}. "
             f"À {principale.get('label', '')} : {round(principale.get('temp', 0))} degrés, "
             f"{principale.get('description', '')}.")
    if diaspora:
        texte += f" À {diaspora.get('label', '')} : {round(diaspora.get('temp', 0))} degrés, {diaspora.get('description', '')}."
    texte += " Que Dieu bénisse votre journée !"

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"date": TODAY, "title": f"Météo du {date_fr}", "text": texte},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    return texte


def _items():
    items = []
    for moment in (config.PRIERE_MOMENTS or ["matin"]):
        items.append((f"content/prayers/{moment}_{TODAY}.json", f"audio/prayers/{moment}_{TODAY}",
                      "priere", f"Prière {moment}"))
    items.append((f"content/testimonies/{TODAY}.json", f"audio/testimonies/{TODAY}", "temoignage", "Témoignage"))
    items.append((f"content/sermons/{TODAY}.json", f"audio/sermons/{TODAY}", "sermon", "Sermon"))
    return items


ITEMS = _items()


def main():
    print(f"\n=== {config.STATION_NOM} — Audios quotidiens ({config.TTS_PROVIDER}) — {TODAY} ===\n")

    meteo_audio = BASE_DIR / f"audio/meteo/{TODAY}.{EXT}"
    if meteo_audio.exists():
        print("Météo: déjà générée")
    else:
        texte = generate_meteo_text()
        if texte:
            kb = tts_engine.synth_to_file(texte, "meteo", meteo_audio)
            print(f"Météo -> {kb} KB")

    total = 0
    for json_rel, mp3_rel_no_ext, role, label in ITEMS:
        json_path = BASE_DIR / json_rel
        mp3_path = BASE_DIR / f"{mp3_rel_no_ext}.{EXT}"

        if mp3_path.exists():
            print(f"{label}: déjà généré")
            total += 1
            continue
        if not json_path.exists():
            print(f"{label}: JSON manquant — {json_path}")
            continue

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
            texte = build_text(data)
            print(f"{label}...")
            kb = tts_engine.synth_to_file(texte, role, mp3_path)
            print(f"  -> {kb} KB")
            total += 1
        except Exception as e:
            print(f"{label}: erreur — {e}")

    print(f"\n{total}/{len(ITEMS)} audios générés (+ météo)")


if __name__ == "__main__":
    main()
