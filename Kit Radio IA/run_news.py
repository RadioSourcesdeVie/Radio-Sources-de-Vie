#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kit Radio IA - Orchestrateur NEWS : récupère les flux RSS, génère les résumés audio + sync RadioDJ."""
from _orchestration_commune import log, lancer

def main():
    log("NEWS")
    lancer("fetch_news.py")
    lancer("generate_resumes.py")
    lancer("sync_radiodj.py")
    print("Nouvelles OK")

if __name__ == "__main__":
    main()
