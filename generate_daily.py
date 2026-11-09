#!/usr/bin/env python3
"""
generate_daily.py — Prière du matin et du soir (10 min chacune)
Radio Sources de Vie Chrétienne
"""
import anthropic, json
from datetime import datetime, timedelta
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")

def _fixer_date(valeur):
    """--date demain  ou  --date 2026-11-09"""
    global TODAY
    if not valeur:
        return
    if valeur.lower() in ("demain", "tomorrow"):
        TODAY = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        datetime.strptime(valeur, "%Y-%m-%d")      # valide le format
        TODAY = valeur
HOUR  = datetime.now().hour

SYSTEM_PASTOR = ("Tu es un pasteur chrétien évangélique francophone. Tu t'adresses aux Haïtiens "
                 "du monde entier : ceux restés en Haïti, et ceux de la diaspora — Canada, "
                 "États-Unis, France, République dominicaine, Chili, Brésil, Antilles, et ailleurs. "
                 "Ne suppose jamais que l'auditeur vit au Canada. Langue: français uniquement.")

def gen(client, prompt, system=SYSTEM_PASTOR, max_tokens=1500):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=max_tokens,
        system=system,
        messages=[{"role":"user","content":prompt}]
    )
    return msg.content[0].text.strip()

def save(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------------------------------------------------------------
# Prieres longues (environ 10 min) construites en 4 mouvements.
# Structure voulue par Souvenan :
#   1. le psaume qui situe l'heure
#   2. une priere biblique qui a change une destinee
#   3. l'intercession pour l'auditeur
#   4. Jesus a deja prie pour toi
# ---------------------------------------------------------------

REGLE_PRIERE = (
    "Tu ecris une priere lue a voix haute a la radio, en francais, "
    "pour les Haitiens du monde entier : ceux d'Haiti comme ceux de la "
    "diaspora, sur tous les continents. N'ecris AUCUN titre, AUCUN numero, "
    "AUCUNE etiquette de structure : seulement la priere elle-meme, "
    "adressee a Dieu a la deuxieme personne. Pas de markdown, pas "
    "d'asterisque. Phrases courtes, rythme lent, ton recueilli. "
    "Cite les versets en Louis Segond, integres naturellement dans "
    "la priere. Ne repete pas les formules d'un mouvement a l'autre. "
)

PRIERES_BIBLIQUES = [
    "Anne a Silo (1 Samuel 1)", "Ezechias malade (2 Rois 20)",
    "Jabets (1 Chroniques 4:10)", "Salomon a Gabaon (1 Rois 3)",
    "Moise pour le peuple (Exode 32)", "Daniel a sa fenetre (Daniel 9)",
    "Elie au Carmel (1 Rois 18)", "Jonas dans le poisson (Jonas 2)",
    "Nehemie devant le roi (Nehemie 1)", "Josaphat devant l'ennemi (2 Chroniques 20)",
    "le brigand sur la croix (Luc 23)", "Etienne mourant (Actes 7)",
    "l'eglise pour Pierre en prison (Actes 12)", "Paul et Silas a minuit (Actes 16)",
]

PSAUMES_MATIN = ["Psaume 5", "Psaume 63", "Psaume 90", "Psaume 143",
                 "Psaume 30", "Psaume 59", "Psaume 92"]
PSAUMES_SOIR  = ["Psaume 4", "Psaume 91", "Psaume 121", "Psaume 127",
                 "Psaume 134", "Psaume 3", "Psaume 141"]

def _mouvements(moment, psaume, histoire):
    """Les 4 consignes, adaptees au matin ou au soir."""
    if moment == "matin":
        cadre = "C'est le matin, l'auditeur se leve et part vers sa journee."
        fin = ("Termine en envoyant l'auditeur dans sa journee sans crainte, "
               "puis conclus par : Au nom de Jesus, amen.")
    else:
        cadre = ("C'est le soir, l'auditeur depose sa journee et se prepare "
                 "a la nuit.")
        fin = ("Termine en confiant la nuit et le sommeil a Dieu, puis "
               "conclus par : Au nom de Jesus, amen.")
    return [
        (f"{REGLE_PRIERE}{cadre} Premier mouvement, 320 mots : ouvre la priere "
         f"en t'appuyant sur le {psaume}. Cite deux versets de ce psaume et "
         f"laisse-les porter la priere. Ne raconte encore aucune histoire."),
        (f"{REGLE_PRIERE}{cadre} Deuxieme mouvement, 380 mots : rappelle a Dieu "
         f"la priere de {histoire}. Raconte brievement la situation, cite le "
         f"verset de sa priere, et montre comment une seule priere a change "
         f"une destinee. Reste dans l'adresse a Dieu, ne bascule pas dans la "
         f"predication."),
        (f"{REGLE_PRIERE}{cadre} Troisieme mouvement, 380 mots : intercede "
         f"concretement pour l'auditeur, ou qu'il soit dans le monde. Ce qu'il "
         f"porte en silence, sa famille, son travail, sa sante, les siens au "
         f"loin. Pense aussi bien a celui qui ecoute depuis Port-au-Prince ou "
         f"Jacmel qu'a celui de Montreal, Miami, Paris, Saint-Domingue ou "
         f"Santiago. N'emploie pas 'ici' ni 'dans ce pays' : l'auditeur peut "
         f"etre n'importe ou. Nomme des situations reelles sans tomber dans la "
         f"liste mecanique, et varie : ne parle pas toujours de migration."),
        (f"{REGLE_PRIERE}{cadre} Quatrieme et dernier mouvement, 320 mots : "
         f"rappelle que Jesus a deja prie pour celui qui ecoute. Appuie-toi sur "
         f"Luc 22:32 et Jean 17:20. Montre que l'intercession du Christ precede "
         f"notre priere. {fin}"),
    ]

def _generer_priere(client, moment):
    import random
    out = f"content/prayers/{moment}_{TODAY}.json"
    if Path(out).exists():
        print(f"⏭️  Prière {moment} déjà générée"); return

    jour = datetime.now().timetuple().tm_yday
    psaume = (PSAUMES_MATIN if moment == "matin" else PSAUMES_SOIR)[jour % 7]
    histoire = PRIERES_BIBLIQUES[jour % len(PRIERES_BIBLIQUES)]
    print(f"{'🌅' if moment=='matin' else '🌙'}  Prière {moment} — "
          f"{psaume}, {histoire}")

    parties = []
    for i, prompt in enumerate(_mouvements(moment, psaume, histoire), 1):
        print(f"   mouvement {i}/4...")
        parties.append(gen(client, prompt, max_tokens=2000).strip())

    contenu = "\n\n".join(parties)
    mots = len(contenu.split())
    titre = ("Prière du Matin" if moment == "matin" else "Prière du Soir")
    save(out, {
        "title": f"{titre} — {TODAY}",
        "date": TODAY,
        "moment": moment,
        "verse": psaume,
        "reference": histoire,
        "content": contenu,
        "words": mots,
        "minutes": round(mots / 140, 1),
    })
    print(f"✅ Prière {moment} → {out}  ({mots} mots, ~{mots/140:.0f} min)")

def generate_prayer_matin(client):
    _generer_priere(client, "matin")

def generate_prayer_soir(client):
    _generer_priere(client, "soir")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True)
    parser.add_argument("--date", default=None,
                        help="demain, ou une date AAAA-MM-JJ")
    args = parser.parse_args()
    _fixer_date(args.date)
    client = anthropic.Anthropic(api_key=args.api_key)
    
    print(f"\n📻 Génération contenu quotidien — {TODAY}\n")
    generate_prayer_matin(client)
    generate_prayer_soir(client)
    print(f"\n✅ Tout généré pour {TODAY}")

if __name__ == "__main__":
    main()
