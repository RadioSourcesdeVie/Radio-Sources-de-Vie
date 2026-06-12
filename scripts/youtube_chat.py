# -*- coding: utf-8 -*-
import time
import requests as http
import mysql.connector

# ---- Reglages YouTube ----
API_KEY = "AIzaSyDziCYy6jT-mVEcHDx8LQZmTWqMAhKj36c"
CHANNEL_ID = "UCxWzOPQv5SbqBThsrKqupJA"
API = "https://www.googleapis.com/youtube/v3"

# ---- Reglages RadioDJ ----
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
    sql = ("SELECT ID, title FROM songs "
           "WHERE title LIKE %s AND enabled = 1 "
           "ORDER BY title LIMIT 1")
    cur.execute(sql, ("%" + recherche + "%",))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return {"id": row[0], "title": row[1]}
    return None


def mettre_en_queue(song_id):
    url = REST_HOST + "/opt"
    params = {"auth": REST_AUTH, "command": "LoadTrackToBottom", "arg": song_id}
    r = http.get(url, params=params, timeout=5)
    return "200" in r.text


def traiter_commande(auteur, texte):
    texte = texte.strip()
    if texte.lower().startswith("!request"):
        recherche = texte[8:].strip()
        if not recherche:
            print(f"  {auteur} a tape !request sans titre.")
            return
        chanson = chercher_chanson(recherche)
        if chanson is None:
            print(f"  Aucune chanson trouvee pour '{recherche}' (demande par {auteur})")
            return
        ok = mettre_en_queue(chanson["id"])
        if ok:
            print(f"  AJOUTEE : {chanson['title']} (demande par {auteur})")
        else:
            print(f"  Trouvee mais erreur d'ajout : {chanson['title']}")
    else:
        print(f"  {auteur}: {texte}")


def trouver_live_video_id():
    url = API + "/search"
    params = {"part": "snippet", "channelId": CHANNEL_ID,
              "eventType": "live", "type": "video", "key": API_KEY}
    data = http.get(url, params=params, timeout=10).json()
    if "error" in data:
        print("ERREUR API :", data["error"].get("message"))
        return None
    i