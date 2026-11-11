#!/usr/bin/env python3
"""
rsdv_ancre.py — L'ancre du jour pour les prieres de Radio Sources de Vie.

Il n'y a AUCUNE liste figee dans ce fichier.

Chaque priere s'appuie sur trois choses, choisies chaque jour dans toute
l'Ecriture, en excluant tout ce qui a deja servi depuis le premier jour :

  1. un THEME, porte par un verset  (ex. « dormir sans peur » — Psaume 4:9)
  2. une PRIERE RAPPORTEE dans la Bible, qui a change une destinee
  3. un TEXTE sur l'intercession du Christ

La memoire vit dans state/deja_servi.json. Elle s'allonge et n'oublie
jamais : au bout d'un an elle contient trois cent soixante-cinq themes,
et le modele recoit la consigne de trouver autre chose.

Si un appel echoue, l'appelant doit retomber sur son ancien comportement.
Une priere ne doit jamais manquer a l'antenne pour un theme.
"""
import json
import re
from datetime import datetime
from pathlib import Path

MEMOIRE = Path("state/deja_servi.json")

# Combien d'entrees passees on montre au modele. La memoire, elle, garde
# tout : ce plafond ne sert qu'a ne pas gonfler le prompt indefiniment.
PLAFOND_PROMPT = 400


# ---------------------------------------------------------------------------
# Memoire
# ---------------------------------------------------------------------------
def _charger():
    if not MEMOIRE.exists():
        return {"themes": [], "figures": [], "christ": []}
    try:
        d = json.loads(MEMOIRE.read_text(encoding="utf-8"))
        for c in ("themes", "figures", "christ"):
            d.setdefault(c, [])
        return d
    except Exception:
        # Fichier illisible : on repart a vide plutot que d'echouer.
        return {"themes": [], "figures": [], "christ": []}


def _ecrire(memoire):
    MEMOIRE.parent.mkdir(parents=True, exist_ok=True)
    MEMOIRE.write_text(
        json.dumps(memoire, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _deja(memoire, categorie, champ):
    """Les valeurs deja servies, les plus recentes en dernier."""
    return [e[champ] for e in memoire.get(categorie, []) if e.get(champ)]


def _liste_pour_prompt(valeurs):
    if not valeurs:
        return "(rien encore — tu as toute l'Ecriture devant toi)"
    return "\n".join(f"- {v}" for v in valeurs[-PLAFOND_PROMPT:])


# ---------------------------------------------------------------------------
# Lecture de la reponse du modele
# ---------------------------------------------------------------------------
def _json_du_modele(brut):
    """Extrait l'objet JSON, meme entoure de texte ou de balises ```."""
    t = brut.strip()
    if "```" in t:
        morceaux = t.split("```")
        for m in morceaux:
            m = m.strip()
            if m.startswith("json"):
                m = m[4:].strip()
            if m.startswith("{"):
                t = m
                break
    d = t.find("{")
    f = t.rfind("}")
    if d == -1 or f == -1 or f < d:
        raise ValueError(f"pas de JSON dans la reponse : {brut[:200]}")
    return json.loads(t[d:f + 1])


def _propre(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().strip('"').strip("«»").strip()


# ---------------------------------------------------------------------------
# Les trois choix du jour
# ---------------------------------------------------------------------------
def _theme(gen, client, moment, memoire):
    quand = "du matin" if moment == "matin" else "du soir"
    cadre = (
        "L'auditeur se leve et part vers sa journee. Le theme doit regarder "
        "ce qui vient : la route, la force, l'envoi, la provision, la "
        "direction, le premier pas."
        if moment == "matin" else
        "L'auditeur depose sa journee et se prepare a la nuit. Le theme doit "
        "regarder ce qui s'acheve : le fardeau pose, le pardon avant la nuit, "
        "le sommeil sans peur, la veille de Dieu, le repos."
    )
    prompt = f"""Tu prepares une priere {quand} diffusee a la radio pour des auditeurs haitiens, en Haiti et dans la diaspora.

{cadre}

Choisis UN theme, et le verset biblique qui le porte.

Le verset peut venir de N'IMPORTE OU dans l'Ecriture : les Psaumes, mais aussi les Lamentations, Esaie, Jeremie, les Proverbes, les Evangiles, les epitres. Ne te rabats pas sur les passages les plus connus par reflexe.

Le theme n'est pas un titre de sermon : c'est ce que la priere apporte a celui qui ecoute, dit en trois a sept mots. Par exemple « dormir sans peur », « etre guide quand on ne voit pas la route », « les compassions qui se renouvellent ».

Themes et versets deja utilises, a NE PAS reprendre :
{_liste_pour_prompt(_deja(memoire, 'themes', 'theme'))}

Versets deja utilises :
{_liste_pour_prompt(_deja(memoire, 'themes', 'reference'))}

Le passage choisi doit porter la consolation, la confiance, la louange ou l'intercession. Ecarte les passages d'imprecation ou de malediction, qui ne conviennent pas a une priere radiodiffusee.

Reponds UNIQUEMENT par un objet JSON :
{{"theme": "le theme en trois a sept mots", "verset": "le texte complet du verset en Louis Segond", "reference": "Livre Chapitre:Verset", "pourquoi": "une phrase disant ce que ce theme apporte a l'auditeur {quand}"}}"""

    d = _json_du_modele(gen(client, prompt, max_tokens=400))
    theme, verset, ref = (_propre(d.get("theme")), _propre(d.get("verset")),
                          _propre(d.get("reference")))
    if not (theme and verset and ref):
        raise ValueError(f"theme incomplet : {d}")
    return {"theme": theme, "verset": verset, "reference": ref,
            "pourquoi": _propre(d.get("pourquoi"))}


def _figure(gen, client, moment, theme, memoire):
    prompt = f"""Dans la Bible, trouve UNE priere rapportee qui a change une destinee, et qui fait echo au theme : « {theme} ».

L'Ecriture en contient des dizaines : Anne, Jabets, Ezechias, Habacuc, Nehemie, Esdras, Elie, Elisee, Jonas, Daniel, Manasse, le centurion, la Cananeenne, Bartimee, le lepreux, Jairus, le brigand sur la croix, Etienne, Corneille, Epaphras, l'eglise d'Actes 4, et bien d'autres. Ne te limite pas a cette enumeration : elle n'est la que pour te montrer l'etendue.

Prieres deja utilisees, a NE PAS reprendre :
{_liste_pour_prompt(_deja(memoire, 'figures', 'figure'))}

Reponds UNIQUEMENT par un objet JSON :
{{"figure": "qui prie, en quelques mots, avec la reference entre parentheses", "reference": "Livre Chapitre:Verset", "verset": "le texte de sa priere en Louis Segond", "destinee": "une phrase disant ce qui a change apres cette priere"}}"""

    d = _json_du_modele(gen(client, prompt, max_tokens=500))
    fig = _propre(d.get("figure"))
    if not fig:
        raise ValueError(f"figure incomplete : {d}")
    return {"figure": fig, "reference": _propre(d.get("reference")),
            "verset": _propre(d.get("verset")),
            "destinee": _propre(d.get("destinee"))}


def _christ(gen, client, theme, memoire):
    prompt = f"""Trouve UN passage du Nouveau Testament qui montre que Jesus-Christ intercede deja pour celui qui ecoute, ou qui porte sa promesse de ne pas l'abandonner. Il doit faire echo au theme : « {theme} ».

Passages deja utilises, a NE PAS reprendre :
{_liste_pour_prompt(_deja(memoire, 'christ', 'reference'))}

Reponds UNIQUEMENT par un objet JSON :
{{"reference": "Livre Chapitre:Verset", "verset": "le texte complet en Louis Segond", "portee": "une phrase disant ce que ce passage assure a l'auditeur"}}"""

    d = _json_du_modele(gen(client, prompt, max_tokens=400))
    ref = _propre(d.get("reference"))
    if not ref:
        raise ValueError(f"texte sur le Christ incomplet : {d}")
    return {"reference": ref, "verset": _propre(d.get("verset")),
            "portee": _propre(d.get("portee"))}


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------
def ancre_du_jour(gen, client, moment, date_cible):
    """
    Renvoie le theme, la figure et le texte sur le Christ du jour, puis
    les inscrit dans la memoire.

    `gen` est la fonction d'appel au modele de l'appelant, de signature
    gen(client, prompt, max_tokens=...) -> str.

    Leve une exception si quoi que ce soit echoue : a l'appelant de
    retomber sur son ancien comportement.
    """
    memoire = _charger()

    theme = _theme(gen, client, moment, memoire)
    figure = _figure(gen, client, moment, theme["theme"], memoire)
    christ = _christ(gen, client, theme["theme"], memoire)

    horodatage = {"date": date_cible, "moment": moment,
                  "ecrit_le": datetime.now().strftime("%Y-%m-%d %H:%M")}
    memoire["themes"].append({**horodatage, **theme})
    memoire["figures"].append({**horodatage, **figure})
    memoire["christ"].append({**horodatage, **christ})
    _ecrire(memoire)

    return theme, figure, christ


def compter():
    """Ce que la memoire contient deja, pour le journal."""
    m = _charger()
    return {c: len(m.get(c, [])) for c in ("themes", "figures", "christ")}
