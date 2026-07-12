# -*- coding: utf-8 -*-
import re
import time
import requests as http
import mysql.connector

API_KEY = "AIzaSyDziCYy6jT-mVEcHDx8LQZmTWqMAhKj36c"
CHANNEL_ID = "UCxWzOPQv5SbqBThsrKqupJA"
API = "https://www.googleapis.com/youtube/v3"

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "radiodj2050RadioSourcesdeVie",
    "user": "root",
    "password": "Samumu76!",
}
REST_HOST = "http://localhost:8080"
REST_AUTH = "changeme"


def chercher_chanson(recherche):
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    sql = ("SELECT ID, title FROM songs WHERE title LIKE %s AND enabled = 1 ORDER BY title LIMIT 1")
    cur.execute(sql, ("%" + recherche + "%",))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {"id": row[0], "title": row[1]}
    return None


def mettre_en_queue(song_id):
    url = REST_HOST + "/opt"
    params = {"auth": REST_AUTH, "command": "LoadTrackToTop", "arg": song_id}
    r = http.get(url, params=params, timeout=5)
    return "200" in r.text


MOT_CLE_PATTERN = re.compile(
    r'(?:!request|!req|!mizik|\brequest\b|\breq\b|\bmizik\b)',
    re.IGNORECASE
)


def traiter_commande(auteur, texte):
    texte = texte.strip()
    match = MOT_CLE_PATTERN.search(texte)
    if match:
        recherche = texte[match.end():].strip()
        if not recherche:
            print("  " + auteur + " a tape !request sans titre.")
            return
        chanson = chercher_chanson(recherche)
        if chanson is None:
            print("  Aucune chanson trouvee pour '" + recherche + "' (demande par " + auteur + ")")
            return
        ok = mettre_en_queue(chanson["id"])
        if ok:
            print("  AJOUTEE : " + chanson["title"] + " (demande par " + auteur + ")")
        else:
            print("  Trouvee mais erreur d'ajout : " + chanson["title"])
    else:
        print("  " + auteur + ": " + texte)


def trouver_live_video_id():
    url = API + "/search"
    params = {"part": "snippet", "channelId": CHANNEL_ID, "eventType": "live", "type": "video", "key": API_KEY}
    data = http.get(url, params=params, timeout=10).json()
    if "error" in data:
        print("ERREUR API :", data["error"].get("message"))
        return None
    items = data.get("items", [])
    if not items:
        return None
    return items[0]["id"]["videoId"]


def trouver_live_chat_id(video_id):
    url = API + "/videos"
    params = {"part": "liveStreamingDetails", "id": video_id, "key": API_KEY}
    data = http.get(url, params=params, timeout=10).json()
    items = data.get("items", [])
    if not items:
        return None
    return items[0].get("liveStreamingDetails", {}).get("activeLiveChatId")


def lire_chat(live_chat_id):
    page_token = None
    print("Lecture du chat... (Ctrl+C pour arreter)")
    print("")
    while True:
        url = API + "/liveChat/messages"
        params = {"liveChatId": live_chat_id, "part": "snippet,authorDetails", "key": API_KEY}
        if page_token:
            params["pageToken"] = page_token
        data = http.get(url, params=params, timeout=10).json()
        if "error" in data:
            print("ERREUR API :", data["error"].get("message"))
            break
        for item in data.get("items", []):
            auteur = item["authorDetails"]["displayName"]
            texte = item["snippet"].get("displayMessage", "")
            traiter_commande(auteur, texte)
        page_token = data.get("nextPageToken")
        attente_ms = data.get("pollingIntervalMillis", 5000)
        time.sleep(max(attente_ms / 1000.0, 10))


print("=" * 50)
print(" Radio Sources de Vie - Bot YouTube")
print("=" * 50)
print("Recherche du live...")
vid = trouver_live_video_id()
if not vid:
    print("Aucun live trouve. Verifie que tu es en direct.")
    input("Entree pour fermer...")
    raise SystemExit
print("Live trouve :", vid)
chat = trouver_live_chat_id(vid)
if not chat:
    print("Pas de chat actif.")
    input("Entree pour fermer...")
    raise SystemExit
print("Chat trouve ! On ecoute les commandes.")
print("")
lire_chat(chat)