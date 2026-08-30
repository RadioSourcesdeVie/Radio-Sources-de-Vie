# -*- coding: utf-8 -*-
"""
====================================================================
KIT RADIO IA - FICHIER DE CONFIGURATION CENTRAL
====================================================================
C'est le SEUL fichier que vous devez modifier pour personnaliser le kit
pour votre station. Tous les scripts lisent leurs informations ici.

Moteur de texte : Claude (Anthropic) — rapide et très économique (modèle Haiku).
Moteur de voix  : au choix ci-dessous — Edge TTS (gratuit, recommandé),
                  ElevenLabs (payant, qualité premium) ou Gemini (payant).
====================================================================
"""

# --------------------------------------------------------------
# 1. IDENTITÉ DE LA STATION
# --------------------------------------------------------------
STATION_NOM = "Radio Ma Station"
STATION_SLOGAN = ""                       # Optionnel
STATION_LANGUE = "français"               # Langue de génération des textes
PAYS_OU_COMMUNAUTE = "notre communauté"   # Ex: "Haïti", "la RD Congo", "nos auditeurs"
NOM_DIASPORA = ""                         # Ex: "la diaspora haïtienne au Canada" — vide si non applicable

# --------------------------------------------------------------
# 2. GÉOGRAPHIE (météo + actualités locales)
# --------------------------------------------------------------
# Format OpenWeatherMap: "Ville,CODE_PAYS" (ISO 3166, ex: HT, CA, FR, CD)
VILLE_PRINCIPALE = {"owm_query": "Port-au-Prince,HT", "label": "Port-au-Prince, Haïti"}

# Ville secondaire / diaspora, optionnelle. Laisser VILLE_DIASPORA = None pour désactiver.
VILLE_DIASPORA = None
# Ex: VILLE_DIASPORA = {"owm_query": "Ottawa,CA", "label": "Ottawa, Canada"}

# --------------------------------------------------------------
# 3. CLÉS API — TEXTE (Claude / Anthropic, obligatoire)
# --------------------------------------------------------------
# Créez une clé sur https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY = "COLLEZ_VOTRE_CLE_ANTHROPIC_ICI"
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# --------------------------------------------------------------
# 4. CLÉ API — MÉTÉO (OpenWeatherMap, gratuite)
# --------------------------------------------------------------
# Créez une clé gratuite sur https://openweathermap.org/api
OWM_API_KEY = "COLLEZ_VOTRE_CLE_OPENWEATHERMAP_ICI"

# --------------------------------------------------------------
# 5. MOTEUR DE VOIX (TTS) — choisissez UN fournisseur
# --------------------------------------------------------------
# "edge"       -> Edge TTS (Microsoft). GRATUIT, aucune clé requise. Recommandé par défaut.
# "elevenlabs" -> ElevenLabs. Payant, voix les plus naturelles. Nécessite ELEVENLABS_API_KEY.
# "gemini"     -> Google Gemini TTS. Payant au-delà du quota gratuit. Nécessite GEMINI_API_KEY.
TTS_PROVIDER = "edge"

# --- Rôles de voix (utilisés quel que soit le fournisseur) ---
# "presentateur_a" / "presentateur_b" : duo du journal du soir et des résumés
# "priere", "sermon", "temoignage", "meteo" : segments dédiés
VOIX_ROLES = ["presentateur_a", "presentateur_b", "priere", "sermon", "temoignage", "meteo"]

# --- Option "edge" (gratuite) : voix Microsoft Edge TTS par rôle ---
# Edge TTS supporte des dizaines de langues (anglais, espagnol, portugais,
# créole n'est pas disponible mais le français d'Haïti "fr-HT" non plus ;
# utilisez alors une voix fr-FR/fr-CA proche). Ce kit fonctionne dans
# N'IMPORTE QUELLE langue proposée par Edge TTS — changez simplement les voix
# ci-dessous ET la valeur STATION_LANGUE en haut de ce fichier (le texte généré
# par Claude suivra automatiquement cette langue).
# Pour voir TOUTES les voix disponibles (100+ langues) :
#   1. pip install edge-tts
#   2. edge-tts --list-voices
# Exemples : "en-US-GuyNeural" (anglais), "es-ES-AlvaroNeural" (espagnol),
#            "pt-BR-AntonioNeural" (portugais), "sw-KE-RafikiNeural" (swahili)
EDGE_VOICES = {
    "presentateur_a": "fr-BE-CharlineNeural",
    "presentateur_b": "fr-CA-AntoineNeural",
    "priere":         "fr-CA-SylvieNeural",
    "sermon":         "fr-FR-HenriNeural",
    "temoignage":     "fr-FR-DeniseNeural",
    "meteo":          "fr-CA-SylvieNeural",
}

# --- Option "elevenlabs" (payante) ---
# Clé sur https://elevenlabs.io/app/settings/api-keys
# Voice ID: dans ElevenLabs, ouvrez une voix > "..." > Copy Voice ID
ELEVENLABS_API_KEY = "COLLEZ_VOTRE_CLE_ELEVENLABS_ICI"
ELEVENLABS_VOICES = {
    "presentateur_a": "COLLEZ_VOICE_ID_ICI",
    "presentateur_b": "COLLEZ_VOICE_ID_ICI",
    "priere":         "COLLEZ_VOICE_ID_ICI",
    "sermon":         "COLLEZ_VOICE_ID_ICI",
    "temoignage":     "COLLEZ_VOICE_ID_ICI",
    "meteo":          "COLLEZ_VOICE_ID_ICI",
}
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# --- Option "gemini" (payante au-delà du quota gratuit) ---
# Clé sur https://aistudio.google.com/apikey
GEMINI_API_KEY = "COLLEZ_VOTRE_CLE_GEMINI_ICI"
GEMINI_VOICES = {
    "presentateur_a": "Aoede",
    "presentateur_b": "Puck",
    "priere":         "Kore",
    "sermon":         "Charon",
    "temoignage":     "Aoede",
    "meteo":          "Kore",
}
GEMINI_TTS_MODEL = "gemini-2.5-flash-preview-tts"

# --------------------------------------------------------------
# 6. PRIÈRES — combien de fois par jour ?
# --------------------------------------------------------------
# Liste libre : mettez-en 1, 2, 3 ou plus. Chaque moment devient un segment
# généré séparément (texte + audio), ex: ["matin"], ["matin","soir"],
# ["matin","midi","soir"], ["aube","matin","midi","soir","nuit"]...
PRIERE_MOMENTS = ["matin", "soir"]

# --------------------------------------------------------------
# 7. SOURCES D'ACTUALITÉS (flux RSS, par catégorie)
# --------------------------------------------------------------
# Chaque catégorie: clé interne, libellé affiché à l'antenne, liste de flux
# {"url":..., "source": "Nom affiché de la source"}. Ajoutez/retirez librement.
# Une catégorie avec une liste vide sera ignorée dans les bulletins.
CATEGORIES_NEWS = {
    "local": {
        "label": "actualités locales",
        "presentateur": "presentateur_a",
        "flux": [
            # {"url": "https://news.google.com/rss/search?q=Ha%C3%AFti&hl=fr&gl=HT&ceid=HT:fr", "source": "Google Actualités"},
        ],
    },
    "chretien": {
        "label": "actualités chrétiennes",
        "presentateur": "presentateur_a",
        "flux": [
            {"url": "https://morningstarnews.org/feed/", "source": "Morning Star News"},
            {"url": "https://www.porteouverte.org/feed/", "source": "Porte Ouverte"},
            {"url": "https://www.info-chretienne.com/feed", "source": "Info Chrétienne"},
        ],
    },
    "monde": {
        "label": "actualités internationales",
        "presentateur": "presentateur_b",
        "flux": [
            {"url": "https://news.un.org/feed/subscribe/fr/news/all/rss.xml", "source": "ONU Info"},
            {"url": "https://www.france24.com/fr/rss", "source": "France 24"},
        ],
    },
    "sport": {
        "label": "actualités sportives",
        "presentateur": "presentateur_b",
        "flux": [
            {"url": "https://news.google.com/rss/search?q=sport&hl=fr", "source": "Google Sport"},
        ],
    },
}

# --------------------------------------------------------------
# 8. HORAIRE DE DIFFUSION (heure locale du serveur) — script orchestrateur à lancer
# --------------------------------------------------------------
HORAIRE = {
    (6,  0):  "run_meteo.py",         # météo + copie vers RadioDJ
    (7,  0):  "run_spirituel.py",     # prières matin/soir + témoignage + sermon (texte + audio)
    (15, 0):  "run_news.py",          # résumés d'actualités par catégorie
    (18, 0):  "run_bulletin_soir.py", # journal du soir complet (duo présentateurs)
    (4,  30, "MON"): "run_sweepers.py",  # sweepers hebdomadaires (voir remarque ci-dessous)
}
# Remarque : les clés à 3 éléments (heure, minute, jour) ne sont utilisées que par
# setup_tasks.py pour une tâche hebdomadaire. Les autres tournent tous les jours.

# --------------------------------------------------------------
# 9. SWEEPERS / STATION ID
# --------------------------------------------------------------
SWEEPER_TAILLE_LOT = 3   # 3 => régénérer chaque semaine ; 10+ => chaque mois

# --------------------------------------------------------------
# 10. RADIODJ (base de données + API REST + dossiers)
# --------------------------------------------------------------
RADIODJ_DB = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "radiodj2050VotreStation",
    "user": "root",
    "password": "COLLEZ_VOTRE_MOT_DE_PASSE_MYSQL_ICI",
}
RADIODJ_REST_HOST = "http://localhost:8080"
RADIODJ_REST_AUTH = "changeme"

# Dossiers RadioDJ (catégories) où chaque audio généré est copié pour l'AutoDJ.
# Créez ces catégories dans RadioDJ et ajoutez-les comme Events programmés
# (Tools > Event Scheduler) pour qu'AutoDJ les diffuse automatiquement.
# Pour les moments de prière définis dans PRIERE_MOMENTS, le dossier utilisé
# est "priere_<moment>" ci-dessous s'il existe, sinon "Priere/Priere du <moment>"
# est utilisé automatiquement — pas besoin de tout lister ici.
RADIODJ_DOSSIERS = {
    "meteo":         "Nouvelles/Meteo",
    "priere_matin":  "Priere/Priere du matin",
    "priere_soir":   "Priere/Priere du soir",
    "temoignage":    "Priere/Temoignage",
    "sermon":        "Sermon",
    "bulletin_soir": "Nouvelles/Bulletin du Soir",
    "resume_local":     "Nouvelles/Resume Local",
    "resume_chretien":  "Nouvelles/Resume Chretien",
    "resume_monde":     "Nouvelles/Resume Monde",
    "resume_sport":     "Nouvelles/Resume Sport",
    "sweepers":      "Nouvelles/Sweepers",
}
