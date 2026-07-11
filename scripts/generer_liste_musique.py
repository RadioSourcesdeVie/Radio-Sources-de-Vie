# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Génère une page web listant les chansons
disponibles pour les requêtes (!request) dans le chat YouTube.

Lit la base RadioDJ (table songs, enabled=1) et écrit un fichier
HTML autonome (recherche instantanée côté client, pas de serveur
requis) que tu peux uploader tel quel sur ton site.

Usage : py generer_liste_musique.py
Sortie : musique.html (à la racine du projet, à côté du dossier scripts)
"""
import mysql.connector
import json
from pathlib import Path

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "database": "radiodj2050RadioSourcesdeVie",
    "user": "root",
    "password": "Samumu76!",
}

SCRIPTS_DIR = Path(__file__).parent
BASE_DIR = SCRIPTS_DIR.parent
SORTIE = BASE_DIR / "musique.html"


def recuperer_chansons():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()

    # On essaie d'abord avec la colonne artist (schema RadioDJ standard).
    # Si elle n'existe pas, on retombe sur title seul.
    try:
        cur.execute(
            "SELECT title, artist FROM songs WHERE enabled = 1 ORDER BY title"
        )
        rows = cur.fetchall()
        chansons = [{"titre": r[0], "artiste": r[1] or ""} for r in rows]
    except mysql.connector.Error:
        conn.rollback()
        cur.execute(
            "SELECT title FROM songs WHERE enabled = 1 ORDER BY title"
        )
        rows = cur.fetchall()
        chansons = [{"titre": r[0], "artiste": ""} for r in rows]

    cur.close()
    conn.close()
    return chansons


def generer_html(chansons):
    data_json = json.dumps(chansons, ensure_ascii=False)

    html = """<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bibliotheque Musicale - Radio Sources de Vie</title>
<style>
  body {
    margin: 0;
    font-family: Georgia, 'Times New Roman', serif;
    background: #1f3b2c;
    color: #f2ead3;
    min-height: 100vh;
  }
  header {
    padding: 32px 20px 16px;
    text-align: center;
  }
  header h1 {
    margin: 0 0 8px;
    font-size: 2em;
  }
  header p {
    opacity: 0.85;
    margin: 0;
  }
  .conteneur {
    max-width: 700px;
    margin: 0 auto;
    padding: 0 20px 60px;
  }
  #recherche {
    width: 100%;
    box-sizing: border-box;
    padding: 14px 16px;
    font-size: 1.1em;
    border-radius: 8px;
    border: none;
    margin-bottom: 20px;
    font-family: inherit;
  }
  #compteur {
    text-align: center;
    opacity: 0.8;
    margin-bottom: 16px;
    font-size: 0.95em;
  }
  #liste {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  #liste li {
    background: rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
  }
  #liste li .titre {
    font-weight: bold;
  }
  #liste li .artiste {
    opacity: 0.75;
    font-size: 0.9em;
    display: block;
  }
  .astuce {
    text-align: center;
    margin-top: 24px;
    opacity: 0.8;
    font-size: 0.9em;
  }
  .astuce code {
    background: rgba(255,255,255,0.12);
    padding: 2px 6px;
    border-radius: 4px;
  }
  #vide {
    text-align: center;
    opacity: 0.7;
    padding: 20px;
    display: none;
  }
</style>
</head>
<body>
<header>
  <h1>Bibliotheque Musicale</h1>
  <p>Radio Sources de Vie - Cherche un titre pour le demander en direct</p>
</header>
<div class="conteneur">
  <input type="text" id="recherche" placeholder="Chercher une chanson ou un artiste...">
  <div id="compteur"></div>
  <ul id="liste"></ul>
  <div id="vide">Aucune chanson trouvee.</div>
  <p class="astuce">
    Pour demander une chanson pendant le direct, tape dans le chat :<br>
    <code>!request &lt;titre de la chanson&gt;</code>
  </p>
</div>

<script>
  const chansons = __DONNEES__;
  const champRecherche = document.getElementById('recherche');
  const liste = document.getElementById('liste');
  const compteur = document.getElementById('compteur');
  const vide = document.getElementById('vide');

  function afficher(filtre) {
    const f = filtre.trim().toLowerCase();
    const filtrees = f
      ? chansons.filter(c =>
          c.titre.toLowerCase().includes(f) ||
          (c.artiste && c.artiste.toLowerCase().includes(f)))
      : chansons;

    liste.innerHTML = '';
    vide.style.display = filtrees.length ? 'none' : 'block';
    compteur.textContent = filtrees.length + ' chanson(s) disponible(s)';

    filtrees.forEach(c => {
      const li = document.createElement('li');
      const spanTitre = document.createElement('span');
      spanTitre.className = 'titre';
      spanTitre.textContent = c.titre;
      li.appendChild(spanTitre);
      if (c.artiste) {
        const spanArtiste = document.createElement('span');
        spanArtiste.className = 'artiste';
        spanArtiste.textContent = c.artiste;
        li.appendChild(spanArtiste);
      }
      liste.appendChild(li);
    });
  }

  champRecherche.addEventListener('input', () => afficher(champRecherche.value));
  afficher('');
</script>
</body>
</html>
"""
    html = html.replace("__DONNEES__", data_json)
    return html


if __name__ == "__main__":
    print("=" * 50)
    print(" Radio Sources de Vie - Generation liste musicale")
    print("=" * 50)
    print("Connexion a la base RadioDJ...")
    chansons = recuperer_chansons()
    print(f"{len(chansons)} chanson(s) trouvee(s) (enabled=1).")

    html = generer_html(chansons)
    SORTIE.write_text(html, encoding="utf-8")
    print(f"Page generee : {SORTIE}")
    print("Il ne reste qu'a uploader ce fichier sur ton site (ex: musique.html).")
