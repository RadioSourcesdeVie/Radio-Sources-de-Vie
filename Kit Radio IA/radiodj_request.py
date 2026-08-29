# -*- coding: utf-8 -*-
"""
Kit Radio IA - Requêtes de chansons vers RadioDJ
Cherche une chanson dans la bibliothèque RadioDJ et l'ajoute à la file d'attente.
Toutes les informations de connexion viennent de config.py (RADIODJ_DB, RADIODJ_REST_HOST).
Usage : python radiodj_request.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

import mysql.connector
import requests as http


def chercher_chanson(recherche):
    conn = mysql.connector.connect(**config.RADIODJ_DB)
    cursor = conn.cursor()
    sql = ("SELECT ID, title FROM songs "
           "WHERE title LIKE %s AND enabled = 1 "
           "ORDER BY title LIMIT 1")
    cursor.execute(sql, ("%" + recherche + "%",))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return {"id": row[0], "title": row[1]}
    return None


def mettre_en_queue(song_id):
    url = config.RADIODJ_REST_HOST + "/opt"
    params = {"auth": config.RADIODJ_REST_AUTH, "command": "LoadTrackToBottom", "arg": song_id}
    reponse = http.get(url, params=params, timeout=5)
    return "200" in reponse.text


def traiter_requete(recherche):
    chanson = chercher_chanson(recherche)
    if chanson is None:
        return "Desole, aucune chanson trouvee pour : " + recherche
    succes = mettre_en_queue(chanson["id"])
    if succes:
        return "Ajoutee a la file : " + chanson["title"] + " (ID " + str(chanson["id"]) + ")"
    else:
        return "Trouvee mais erreur lors de l'ajout : " + chanson["title"]


if __name__ == "__main__":
    print("=" * 50)
    print(f" {config.STATION_NOM} - Test de requete")
    print("=" * 50)
    print("Tape un nom de chanson, ou 'q' pour quitter.")
    print("")
    while True:
        recherche = input("Chanson demandee > ").strip()
        if recherche.lower() == "q":
            print("Au revoir !")
            break
        if recherche == "":
            continue
        message = traiter_requete(recherche)
        print("  -> " + message)
        print("")
