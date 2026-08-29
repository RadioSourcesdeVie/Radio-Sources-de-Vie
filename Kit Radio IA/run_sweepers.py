#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kit Radio IA - Orchestrateur SWEEPERS : régénère le lot hebdomadaire/mensuel."""
from _orchestration_commune import log, lancer

def main():
    log("SWEEPERS")
    lancer("generate_sweepers.py")
    print("Sweepers OK")

if __name__ == "__main__":
    main()
