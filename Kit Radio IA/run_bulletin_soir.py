#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kit Radio IA - Orchestrateur JOURNAL DU SOIR : réutilise les news du jour, génère le bulletin + sync RadioDJ."""
from _orchestration_commune import log, lancer

def main():
    log("BULLETIN_SOIR")
    lancer("generate_bulletin_soir.py")
    lancer("sync_radiodj.py")
    print("Journal du Soir OK")

if __name__ == "__main__":
    main()
