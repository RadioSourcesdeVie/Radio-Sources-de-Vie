#!/usr/bin/env python3
"""
fetch_weather.py — Météo Ottawa + Port-au-Prince → weather.json
Usage: python fetch_weather.py --api-key VOTRE_CLE_OWM
"""
import json, sys, argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("pip install requests")

BASE = "https://api.openweathermap.org/data/2.5/weather"
CITIES = {
    "ottawa": {"q": "Ottawa,CA", "label": "Ottawa, Canada"},
    "pap":    {"q": "Port-au-Prince,HT", "label": "Port-au-Prince, Haïti"},
}

def fetch(api_key, city_conf):
    url = f"{BASE}?q={city_conf['q']}&appid={api_key}&units=metric&lang=fr"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    d = r.json()
    desc = d["weather"][0]["description"]
    return {
        "label":       city_conf["label"],
        "temp":        d["main"]["temp"],
        "feels_like":  d["main"]["feels_like"],
        "humidity":    d["main"]["humidity"],
        "description": desc.capitalize(),
        "wind_kmh":    round(d["wind"]["speed"] * 3.6, 1),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--output", default="weather.json")
    args = parser.parse_args()

    result = {"updated": datetime.utcnow().isoformat() + "Z"}
    for key, conf in CITIES.items():
        try:
            result[key] = fetch(args.api_key, conf)
            print(f"✅  {conf['label']}: {result[key]['temp']:.0f}°C — {result[key]['description']}")
        except Exception as e:
            print(f"⚠️  {conf['label']}: erreur — {e}")
            result[key] = {"description": "Indisponible", "temp": 0}

    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾  Sauvegardé → {args.output}")

if __name__ == "__main__":
    main()
