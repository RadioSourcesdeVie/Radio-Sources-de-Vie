# -*- coding: utf-8 -*-
import requests as http

API_KEY = "AIzaSyDziCYy6jT-mVEcHDx8LQZmTWqMAhKj36c"
NOM_CHAINE = "Radio Sources de Vie"

API = "https://www.googleapis.com/youtube/v3"

print("Recherche de la chaine :", NOM_CHAINE)
print("")

url = f"{API}/search"
params = {
    "part": "snippet",
    "q": NOM_CHAINE,
    "type": "channel",
    "maxResults": 5,
    "key": API_KEY,
}

r = http.get(url, params=params, timeout=10)
data = r.json()

if "error" in data:
    print("ERREUR :", data["error"].get("message", data["error"]))
else:
    items = data.get("items", [])
    if not items:
        print("Aucune chaine trouvee.")
    else:
        print("Chaines trouvees (la tienne est probablement la 1ere) :\n")
        for i, item in enumerate(items, 1):
            titre = item["snippet"]["title"]
            cid = item["snippet"]["channelId"]
            print(f"  {i}. {titre}")
            print(f"     ID = {cid}\n")

        print("-> Copie l'ID (UC...) de TA chaine.")

input("\nAppuie sur Entree pour fermer...")