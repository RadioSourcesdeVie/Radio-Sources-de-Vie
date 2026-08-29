#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kit Radio IA - Orchestrateur SPIRITUEL : prières, témoignage, sermon (texte + audio) + sync RadioDJ."""
from _orchestration_commune import log, lancer

def main():
    log("SPIRITUEL")
    lancer("generate_content.py", "--type", "all")
    lancer("generate_sermon.py")
    lancer("generate_daily_audio.py")
    lancer("sync_radiodj.py")
    print("Spirituel OK")

if __name__ == "__main__":
    main()
