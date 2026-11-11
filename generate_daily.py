#!/usr/bin/env python3
"""
generate_daily.py — Prière du matin et du soir (10 min chacune)
Radio Sources de Vie Chrétienne
"""
import anthropic, json
from datetime import datetime, timedelta
from pathlib import Path

TODAY = datetime.now().strftime("%Y-%m-%d")

import rsdv_ancre


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
                 "du monde entier : ceux restés en Haïti comme ceux de la diaspora. "
                 "Ne suppose jamais où vit l'auditeur, et n'énumère jamais de villes "
                 "ni de pays : parle à une personne, pas à une carte. "
                 "Langue: français uniquement.")

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
    "N'ENUMERE AUCUN LIEU : ni ville, ni pays, ni region, ni continent, "
    "et jamais une suite de lieux relies par « de... a... ». N'ecris ni "
    "« ici » ni « la-bas ». Si un lieu est vraiment necessaire, un seul, "
    "glisse dans une phrase, jamais en liste. "
    "N'ECRIS PAS de catalogue en « Ceux qui... Ceux qui... » : au plus deux ou "
    "trois situations, chacune ecrite en entier, comme on parle de quelqu'un "
    "qu'on connait. "
)

PRIERES_BIBLIQUES = [
    "Anne a Silo (1 Samuel 1)", "Ezechias malade (2 Rois 20)",
    "Jabets (1 Chroniques 4:10)", "Salomon a Gabaon (1 Rois 3)",
    "Moise pour le peuple (Exode 32)", "Daniel a sa fenetre (Daniel 9)",
    "Elie au Carmel (1 Rois 18)", "Jonas dans le poisson (Jonas 2)",
    "Nehemie devant le roi (Nehemie 1)", "Josaphat devant l'ennemi (2 Chroniques 20)",
    "le brigand sur la croix (Luc 23)", "Etienne mourant (Actes 7)",
    "l'eglise pour Pierre en prison (Actes 12)", "Paul et Silas a minuit (Actes 16)",
    "Abraham intercedant pour Sodome (Genese 18)",
    "Jacob luttant jusqu'a l'aube (Genese 32)",
    "Gedeon demandant un signe (Juges 6)",
    "Samson une derniere fois (Juges 16)",
    "David apres sa faute (Psaume 51)",
    "Asa face a l'armee immense (2 Chroniques 14)",
    "Manasse dans les chaines (2 Chroniques 33)",
    "Esdras et la honte du peuple (Esdras 9)",
    "Job pour ses amis (Job 42)",
    "Habacuc dans l'attente (Habacuc 3)",
    "les trois Hebreux devant la fournaise (Daniel 3)",
    "la Cananeenne pour sa fille (Matthieu 15)",
    "le pere de l'enfant epileptique (Marc 9)",
    "Bartimee criant sur la route (Marc 10)",
    "le publicain au fond du temple (Luc 18)",
    "Corneille dans sa maison (Actes 10)",
]

PSAUMES_MATIN = ["Psaume 5", "Psaume 63", "Psaume 90", "Psaume 143",
                 "Psaume 30", "Psaume 59", "Psaume 92", "Psaume 19",
                 "Psaume 57", "Psaume 108", "Psaume 118", "Psaume 103",
                 "Psaume 145", "Psaume 36"]
PSAUMES_SOIR  = ["Psaume 4", "Psaume 91", "Psaume 121", "Psaume 127",
                 "Psaume 134", "Psaume 3", "Psaume 141", "Psaume 42",
                 "Psaume 62", "Psaume 77", "Psaume 130", "Psaume 131",
                 "Psaume 139", "Psaume 16"]

# Le dernier mouvement rappelle que Christ intercede deja.
# Sans rotation, chaque priere finirait sur Pierre et Jean 17.
TEXTES_CHRIST = [
    "Luc 22:32 — J'ai prie pour toi, afin que ta foi ne defaille point",
    "Jean 17:20 — ceux qui croiront en moi par leur parole",
    "Romains 8:34 — Christ est a la droite de Dieu et intercede pour nous",
    "Hebreux 7:25 — toujours vivant pour interceder en leur faveur",
    "Hebreux 4:15-16 — un souverain sacrificateur compatissant",
    "1 Jean 2:1 — nous avons un avocat aupres du Pere",
    "Esaie 53:12 — il a intercede pour les coupables",
    "Luc 23:34 — Pere, pardonne-leur",
    "Jean 14:16 — je prierai le Pere, il vous donnera un autre consolateur",
    "Romains 8:26 — l'Esprit intercede par des soupirs inexprimables",
    "Hebreux 9:24 — il comparait pour nous devant la face de Dieu",
    "Jean 17:9-11 — je prie pour ceux que tu m'as donnes",
    "Jean 17:15 — je ne te prie pas de les oter du monde",
    "Jean 17:24 — que la ou je suis, ils soient aussi avec moi",
    "Hebreux 5:7 — des prieres avec de grands cris et des larmes",
    "Luc 22:41-44 — il priait plus instamment a Gethsemane",
    "Marc 1:35 — il se leva avant le jour pour prier a l'ecart",
    "Luc 6:12 — il passa toute la nuit a prier Dieu",
    "Jean 11:41-42 — Pere, je Te rends graces de ce que Tu m'as exauce",
    "Ephesiens 2:18 — par lui nous avons acces aupres du Pere",
    "Apocalypse 8:3-4 — les prieres des saints montent devant Dieu",
    "Jean 16:26-27 — le Pere lui-meme vous aime",
]

def _deja_servis(champ, combien):
    """
    Ce qui a servi recemment, pour ne pas le reprendre.
    Tri par DATE : un tri par nom mettrait tous les 'matin' avant les 'soir'.
    """
    import glob, re as _re
    def _cle(f):
        m = _re.search(r"(\d{4}-\d{2}-\d{2})", f)
        return (m.group(1) if m else "", "0" if "matin" in f else "1")
    vus = []
    for f in sorted(glob.glob("content/prayers/*.json"), key=_cle)[-combien:]:
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
            if d.get(champ):
                vus.append(d[champ])
        except Exception:
            pass
    return set(vus)

def _choisir(pool, champ, date_cible, decalage, fenetre):
    """
    Rotation deterministe calee sur la DATE DE LA PRIERE, pas sur le jour
    ou le script tourne. Le decalage separe le matin du soir. On avance
    ensuite d'un cran tant que la valeur a servi tout recemment.
    """
    rang = datetime.strptime(date_cible, "%Y-%m-%d").toordinal() + decalage
    recents = _deja_servis(champ, fenetre)
    n = len(pool)
    for pas in range(n):
        choix = pool[(rang + pas) % n]
        if choix not in recents:
            return choix
    return pool[rang % n]          # tout a servi : on reprend la rotation

def _mouvements_theme(moment, theme, figure, christ):
    """
    Les 4 consignes, baties sur le THEME du jour.

    Le matin et le soir ne recoivent plus la meme consigne : le matin
    regarde ce qui vient, le soir ce qui s'acheve. Sans cela les deux
    prieres d'une meme journee sortaient jumelles.
    """
    if moment == "matin":
        cadre = (
            "C'est le matin, l'auditeur se leve. Il n'a pas encore vecu sa "
            "journee : n'ecris donc pas qu'il est epuise par elle. Le ton "
            "est celui de l'envoi et de l'attente, pas de la lamentation."
        )
        fin = ("Termine en envoyant l'auditeur dans sa journee sans crainte, "
               "puis conclus par : Au nom de Jesus, amen.")
    else:
        cadre = (
            "C'est le soir, l'auditeur depose la journee qu'il vient de "
            "vivre. Le ton est celui du depot et du repos."
        )
        fin = ("Termine en confiant la nuit et le sommeil a Dieu, puis "
               "conclus par : Au nom de Jesus, amen.")

    sujet = theme["theme"]
    return [
        (f"{REGLE_PRIERE}{cadre}\n\n"
         f"Toute la priere d'aujourd'hui porte sur ce theme : {sujet}.\n"
         f"Le verset qui le porte : {theme['verset']} ({theme['reference']}).\n\n"
         f"Premier mouvement, 320 mots : ouvre la priere sur ce theme, en "
         f"t'appuyant sur ce verset. Cite-le, et laisse-le porter l'ouverture. "
         f"Ne raconte encore aucune histoire, et ne parle d'aucun lieu."),

        (f"{REGLE_PRIERE}{cadre}\n\n"
         f"Theme du jour : {sujet}.\n\n"
         f"Deuxieme mouvement, 380 mots : rappelle a Dieu cette priere de "
         f"l'Ecriture — {figure['figure']}. Sa priere : {figure['verset']} "
         f"({figure['reference']}). Ce qui a change ensuite : "
         f"{figure['destinee']}.\n"
         f"Raconte brievement la situation, cite sa priere, et montre comment "
         f"une seule priere a change une destinee. Relie-la au theme du jour. "
         f"Reste dans l'adresse a Dieu, ne bascule pas dans la predication."),

        (f"{REGLE_PRIERE}{cadre}\n\n"
         f"Theme du jour : {sujet}.\n\n"
         f"Troisieme mouvement, 380 mots : intercede pour l'auditeur sur ce "
         f"theme precis. Ce qu'il porte en silence, sa famille, son travail, "
         f"sa sante, les siens au loin.\n"
         f"Choisis deux ou trois personnes reelles et ecris-les vraiment : une "
         f"mere, un homme devant une porte fermee, quelqu'un qui attend une "
         f"nouvelle. Donne-leur assez de chair pour qu'on les voie. "
         f"N'emploie ni « ici » ni « dans ce pays » : l'auditeur peut etre "
         f"n'importe ou, et tu ne dois pas le situer."),

        (f"{REGLE_PRIERE}{cadre}\n\n"
         f"Theme du jour : {sujet}.\n\n"
         f"Quatrieme et dernier mouvement, 320 mots : rappelle que Jesus a "
         f"deja prie pour celui qui ecoute. Appuie-toi UNIQUEMENT sur ce "
         f"passage : {christ['verset']} ({christ['reference']}). Ce qu'il "
         f"assure : {christ['portee']}.\n"
         f"N'emploie aucun autre texte sur l'intercession du Christ. Montre "
         f"que son intercession precede notre priere, et relie-la au theme du "
         f"jour. {fin}"),
    ]


def _mouvements_psaume(moment, psaume, histoire, texte_christ):
    """
    FILET DE SECURITE — l'ancienne construction, batie sur un psaume tire
    des listes. Elle ne sert que si le choix du theme echoue. Une priere
    ne doit jamais manquer a l'antenne.
    """
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
         f"rappelle que Jesus a deja prie pour celui qui ecoute. Appuie-toi "
         f"UNIQUEMENT sur ce passage : {texte_christ}. N'emploie aucun autre "
         f"texte sur l'intercession du Christ, et surtout pas Luc 22:32 ni "
         f"Jean 17:20 s'ils ne sont pas celui-ci. Montre que l'intercession du "
         f"Christ precede notre priere. {fin}"),
    ]

# ---------------------------------------------------------------------------
# Appel a l'action lu a la fin de chaque priere (texte + audio).
# Texte fixe : aucun appel a l'IA, aucun cout. Pour le modifier, editer ici.
# ---------------------------------------------------------------------------
OUTRO_MATIN = (
    "Avant de partir vivre ta journée, fais une chose pour quelqu'un d'autre : "
    "écris un prénom dans les commentaires. Juste un prénom. C'est celui que je "
    "porterai devant Dieu aujourd'hui, à ta place.\n\n"
    "Et si tu connais quelqu'un qui s'est levé ce matin sans force, envoie-lui ce "
    "lien. Tu n'as pas besoin de trouver les mots : la prière les a déjà trouvés "
    "pour toi.\n\n"
    "Reviens demain matin. Une âme qu'on nourrit un seul jour reste affamée. "
    "Abonne-toi à Radio Sources de Vie et active la cloche : demain, la prière "
    "sera déjà là avant même que tu la cherches."
)

OUTRO_SOIR = (
    "Avant de poser ton téléphone, laisse un prénom dans les commentaires. Celui "
    "de quelqu'un qui traverse une nuit difficile. Je le lirai, et je le "
    "porterai.\n\n"
    "Si cette prière t'a rejoint, elle peut en rejoindre un autre. Partage-la avec "
    "celui qui, ce soir, n'arrive pas à fermer les yeux.\n\n"
    "Et reviens demain soir. On ne bâtit pas une paix solide en une seule nuit : "
    "on la bâtit soir après soir, comme on pose une pierre sur une autre. "
    "Abonne-toi à Radio Sources de Vie pour ne plus avoir à la chercher : elle "
    "t'attendra ici, à la même heure."
)

OUTROS = {"matin": OUTRO_MATIN, "soir": OUTRO_SOIR}


def _titrer(client, moment, texte):
    """
    Un titre de quelques mots, propre a la priere du jour.
    Calcule AVANT l'ajout de l'outro : l'outro est identique chaque jour
    et fausserait le titre.
    Si l'appel echoue, on retombe sur l'ancien format date — la priere
    elle-meme ne doit jamais etre perdue pour un titre.
    """
    recents = _deja_servis("sujet", 14)
    eviter = "\n".join(f"- {x}" for x in sorted(recents)) if recents else "(aucun)"
    quand = "du matin" if moment == "matin" else "du soir"
    prompt = (
        f"Voici une priere {quand} diffusee a la radio.\n\n"
        f"{texte[:2500]}\n\n"
        "Donne-lui un titre de trois a sept mots, en francais, qui dit ce que "
        "cette priere apporte a celui qui l'ecoute.\n\n"
        "Regles :\n"
        "- Pas de guillemets, pas de point final.\n"
        "- N'ecris jamais 'Priere du matin' ni 'Priere du soir' dans le titre.\n"
        "- Pas de reference biblique, pas de chiffre, pas de date.\n"
        "- Titres deja utilises ces deux dernieres semaines, a ne pas reprendre :\n"
        f"{eviter}\n\n"
        "Reponds uniquement par le titre, rien d'autre."
    )
    try:
        brut = gen(client, prompt, max_tokens=60)
    except Exception as e:
        print(f"   titre : echec ({e}) — on garde la date")
        return TODAY
    titre = brut.strip().strip('"').strip("\u201c\u201d").rstrip(".").split("\n")[0]
    return titre[:80] if titre else TODAY


def _generer_priere(client, moment):
    import random
    out = f"content/prayers/{moment}_{TODAY}.json"
    if Path(out).exists():
        print(f"⏭️  Prière {moment} déjà générée"); return

    icone = "🌅" if moment == "matin" else "🌙"

    # --- L'ancre du jour : un theme, une priere de l'Ecriture, un texte du
    #     Christ, choisis dans toute la Bible sans liste figee.
    sujet = None
    try:
        theme, figure, christ = rsdv_ancre.ancre_du_jour(
            gen, client, moment, TODAY)
        sujet = theme["theme"]
        psaume = f"{theme['verset']} ({theme['reference']})"
        histoire = figure["figure"]
        texte_christ = f"{christ['verset']} ({christ['reference']})"
        vus = rsdv_ancre.compter()
        print(f"{icone}  Prière {moment} — {sujet}")
        print(f"   verset : {theme['reference']}")
        print(f"   prière : {histoire}")
        print(f"   Christ : {christ['reference']}")
        print(f"   mémoire : {vus['themes']} thèmes déjà servis")
        consignes = _mouvements_theme(moment, theme, figure, christ)
    except Exception as e:
        # Filet de securite : on repasse par les anciennes listes plutot
        # que de laisser l'antenne sans priere.
        print(f"⚠️  thème indisponible ({e}) — on repasse par les listes")
        dec = 0 if moment == "matin" else 7
        psaumes = PSAUMES_MATIN if moment == "matin" else PSAUMES_SOIR
        psaume   = _choisir(psaumes,           "verse",        TODAY, dec, 10)
        histoire = _choisir(PRIERES_BIBLIQUES, "reference",    TODAY, dec, 12)
        texte_christ = _choisir(TEXTES_CHRIST, "texte_christ", TODAY, dec, 10)
        print(f"{icone}  Prière {moment} — {psaume} | {histoire}")
        consignes = _mouvements_psaume(moment, psaume, histoire, texte_christ)

    parties = []
    for i, prompt in enumerate(consignes, 1):
        print(f"   mouvement {i}/4...")
        parties.append(gen(client, prompt, max_tokens=2000).strip())

    contenu = "\n\n".join(parties)

    # Le theme EST le titre. S'il manque, on le calcule sur le texte.
    if not sujet:
        print("   titre...")
        sujet = _titrer(client, moment, contenu)
    print(f"   titre : {sujet}")

    # Appel a l'action : lu dans l'audio ET affiche sur le site
    contenu += "\n\n" + OUTROS[moment]
    mots = len(contenu.split())
    titre = ("Prière du Matin" if moment == "matin" else "Prière du Soir")
    save(out, {
        "title": f"{titre} — {sujet}",
        "sujet": sujet,
        "date": TODAY,
        "moment": moment,
        "verse": psaume,
        "reference": histoire,
        "texte_christ": texte_christ,
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
    parser.add_argument("--type", default="all", choices=["matin", "soir", "all"],
                        help="quelle priere generer")
    args = parser.parse_args()
    _fixer_date(args.date)
    client = anthropic.Anthropic(api_key=args.api_key)
    
    print(f"\n📻 Génération contenu quotidien — {TODAY}\n")
    if args.type in ("matin", "all"):
        generate_prayer_matin(client)
    if args.type in ("soir", "all"):
        generate_prayer_soir(client)
    print(f"\n✅ Tout généré pour {TODAY}")

if __name__ == "__main__":
    main()
