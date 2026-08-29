#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kit Radio IA - Orchestrateur MÉTÉO : récupère la météo, génère l'audio, synchronise RadioDJ."""
from _orchestration_commune import log, lancer

def main():
    log("METEO")
    lancer("fetch_weather.py")
    lancer("generate_daily_audio.py")
    lancer("sync_radiodj.py")
    print("Météo OK")

if __name__ == "__main__":
    main()
