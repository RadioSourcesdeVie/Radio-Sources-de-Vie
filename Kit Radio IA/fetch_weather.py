#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Météo -> weather.json
Ville(s) définies dans config.py (VILLE_PRINCIPALE, VILLE_DIASPORA).
Usage : python fetch_weather.py
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

import requests

BASE_DIR = Path(__file__).parent.parent
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


def fetch(ville: dict) -> dict:
    url = f"{BASE_URL}?q={ville['owm_query']}&appid={config.OWM_API_KEY}&units=metric&lang=fr"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    d = r.json()
    desc = d["weather"][0]["description"]
    return {
        "label": ville["label"],
        "temp": d["main"]["temp"],
        "feels_like": d["main"]["feels_like"],
        "humidity": d["main"]["humidity"],
        "description": desc.capitalize(),
        "wind_kmh": round(d["wind"]["speed"] * 3.6, 1),
    }


def main():
    villes = {"principale": config.VILLE_PRINCIPALE}
    if config.VILLE_DIASPORA:
        villes["diaspora"] = config.VILLE_DIASPORA

    result = {"updated": datetime.utcnow().isoformat() + "Z"}
    for cle, ville in villes.items():
        try:
            result[cle] = fetch(ville)
            print(f"  {ville['label']}: {result[cle]['temp']:.0f}°C — {result[cle]['description']}")
        except Exception as e:
            print(f"  {ville['label']}: erreur — {e}")
            result[cle] = {"label": ville["label"], "description": "Indisponible", "temp": 0}

    out = BASE_DIR / "weather.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Sauvegardé -> {out}")


if __name__ == "__main__":
    main()
