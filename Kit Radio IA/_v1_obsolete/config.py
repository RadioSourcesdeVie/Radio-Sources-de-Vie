# -*- coding: utf-8 -*-
"""
====================================================================
KIT RADIO IA - FICHIER DE CONFIGURATION CENTRAL
====================================================================
C'est le SEUL fichier que vous devez modifier pour personnaliser
le kit pour votre station. Tous les scripts lisent leurs
informations ici (nom, ville, sources, horaire, accès techniques).

Remplissez chaque section ci-dessous, puis lancez les scripts.
====================================================================
"""

# --------------------------------------------------------------
# 1. IDENTITÉ DE LA STATION
# --------------------------------------------------------------
STATION_NOM = "Radio Ma Station"          # Nom complet annoncé à l'antenne
STATION_SLOGAN = ""                       # Optionnel, ex: "La radio qui bénit"
STATION_LANGUE = "français"               # Langue de génération (ex: français, anglais, espagnol)

# --------------------------------------------------------------
# 2. GÉOGRAPHIE (météo + actualités locales)
# --------------------------------------------------------------
# Ville principale de la station (météo + actualités locales)
VILLE_PRINCIPALE_NOM = "Ma Ville"         # Nom affiché à l'antenne, ex: "Port-au-Prince, Haïti"
VILLE_PRINCIPALE_API = "Port-au-Prince"   # Nom utilisé pour l'API météo (wttr.in) - sans accents de préférence

# Ville secondaire / diaspora (optionnelle). Laisser VILLE_DIASPORA_NOM = "" pour désactiver.
VILLE_DIASPORA_NOM = ""                   # Ex: "Ottawa, Canada"
VILLE_DIASPORA_API = ""                   # Ex: "Ottawa"

# Nom de la communauté/pays utilisé dans les textes générés (prières, intercession)
PAYS_OU_COMMUNAUTE = "notre pays"         # Ex: "Haïti", "la République Démocratique du Congo"
NOM_DIASPORA = ""                         # Ex: "la diaspora haïtienne" - laisser vide si non applicable

# --------------------------------------------------------------
# 3. SOURCES D'ACTUALITÉS (flux RSS)
# --------------------------------------------------------------
# Ajoutez/retirez des flux RSS librement. Testez chaque flux dans un navigateur
# avant de l'ajouter (il doit afficher du XML, pas une erreur).
FLUX_LOCAL = [
    # Ex: "https://news.google.com/rss/search?q=Ha%C3%AFti&hl=fr&gl=HT&ceid=HT:fr",
]

FLUX_INTERNATIONAL = [
    "https://news.un.org/feed/subscribe/fr/news/all/rss.xml",
    "https://www.francetvinfo.fr/monde.rss",
    "https://www.rfi.fr/fr/monde/rss",
]

FLUX_CHRETIEN = [
    "https://www.info-chretienne.com/feed",
    "https://morningstarnews.org/feed",
    "https://www.porteouverte.org/feed",
    "https://www.christianpost.com/feed",
]

# --------------------------------------------------------------
# 4. IA - GÉNÉRATION DE TEXTE ET VOIX (Google Gemini)
# --------------------------------------------------------------
# Obtenez une clé gratuite sur https://aistudio.google.com/apikey
GEMINI_API_KEY = "COLLEZ_VOTRE_CLE_API_GEMINI_ICI"

VOICE_NAME = "Aoede"                      # Voix Gemini TTS: Aoede, Puck, Charon, Kore, Fenrir, etc.
TTS_MODEL_PRIMARY = "gemini-2.5-flash-preview-tts"
TTS_MODEL_FALLBACK = "gemini-2.5-pro-preview-tts"
TEXT_MODEL = "gemini-2.5-flash"

# --------------------------------------------------------------
# 5. HORAIRE DE DIFFUSION QUOTIDIEN (heure locale du serveur)
# --------------------------------------------------------------
# Format (heure, minute) : script. Modifiez les heures ou retirez une ligne
# si un segment n'est pas utilisé.
HORAIRE = {
    (5,  0):  "priere_matin.py",
    (7,  0):  "bulletin_matin.py",
    (9,  30): "sermon_matin.py",
    (17, 0):  "bulletin_soir.py",
    (18, 0):  "temoignage.py",
    (20, 0):  "sermon_soir.py",
    (21, 0):  "priere_soir.py",
}

# --------------------------------------------------------------
# 6. RADIODJ (base de données + API REST)
# --------------------------------------------------------------
RADIODJ_DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "radiodj2050VotreStation",   # Nom de la base créée par RadioDJ
    "user": "root",
    "password": "COLLEZ_VOTRE_MOT_DE_PASSE_MYSQL_ICI",
}

RADIODJ_REST_HOST = "http://localhost:8080"
RADIODJ_REST_AUTH = "changeme"            # Mot de passe REST défini dans RadioDJ (Options > REST API)

# Dossiers RadioDJ (catégories/événements) où les MP3 générés sont copiés pour l'AutoDJ.
# Ces dossiers doivent exister dans votre bibliothèque RadioDJ et être ajoutés
# comme événements programmés dans RadioDJ (voir guide d'installation, étape 6).
RADIODJ_DOSSIERS = {
    "meteo":            "Nouvelles/Meteo",
    "resume_local":     "Nouvelles/Nouvelle Locale",
    "resume_monde":     "Nouvelles/Nouvelle du Monde",
    "resume_chretien":  "Nouvelles/Nouvelle Chretienne",
    "priere_matin":     "Priere/Priere du matin",
    "priere_soir":      "Priere/Priere du soir",
    "temoignage":       "Priere/Temoignage",
}


# --------------------------------------------------------------
# 7. SWEEPERS / STATION ID (voix Microsoft Edge TTS, gratuite)
# --------------------------------------------------------------
# Génère de courts sweepers "Le saviez-vous ?" avec verset biblique.
# Texte généré par Gemini (section 4 ci-dessus) ; voix par Edge TTS (gratuit, aucune clé requise).
SWEEPER_TAILLE_LOT = 3             # 3 => régénérer chaque semaine ; 10+ => chaque mois
SWEEPER_VOIX_PRINCIPALE = "fr-FR-HenriNeural"     # voix Edge TTS, langue principale
SWEEPER_DOSSIER_PRINCIPAL = "Nouvelles/Sweepers"  # dossier RadioDJ pour les sweepers

# Langue secondaire optionnelle (ex: pour une diaspora anglophone). Laisser
# SWEEPER_LANGUE_SECONDAIRE = "" pour désactiver.
SWEEPER_LANGUE_SECONDAIRE = ""                    # Ex: "anglais"
SWEEPER_VOIX_SECONDAIRE = "en-US-GuyNeural"
SWEEPER_DOSSIER_SECONDAIRE = "Nouvelles/SweepersEN"
