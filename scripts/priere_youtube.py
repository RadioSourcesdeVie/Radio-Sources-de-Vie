# -*- coding: utf-8 -*-
"""
Génère les audios des prières YouTube (Radio Sources de Vie) avec Edge TTS.

Format des fichiers .txt déposés dans "scripts_a_generer" :
    [TITRE]
    La prière de Rachel
    [VOIX]
    femme            (ou : homme / fr-FR-HenriNeural / fr-FR-VivienneMultilingualNeural)
    [PRIERE]
    ... texte de la prière longue ...
    [SHORT]
    ... texte du short 1 ...
    [SHORT]
    ... texte du short 2 ...
    [SHORT]
    ... texte du short 3 ...
"""
import asyncio
import re
import shutil
import sys
import traceback
import unicodedata
from pathlib import Path

# ---------- Dossiers ----------
BASE = Path(r"D:\Audio pour Video shorts")
DOSSIER_PRIERES = BASE / "Prières qui ont changé une destinée"
DOSSIER_SCRIPTS = DOSSIER_PRIERES / "scripts_a_generer"
DOSSIER_FAITS = DOSSIER_SCRIPTS / "deja_generes"
DOSSIER_SHORTS = BASE / "Audio short"

# ---------- Voix ----------
VOIX_HOMME = "fr-FR-HenriNeural"
VOIX_FEMME = "fr-FR-VivienneMultilingualNeural"
VITESSE = "-5%"   # un peu plus lent pour la prière


def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def lire(fichier):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return fichier.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Encodage du fichier illisible")


def analyser(texte):
    """Retourne une liste de (BALISE, contenu)."""
    sections, courant, lignes = [], None, []
    for ligne in texte.splitlines():
        m = re.match(r"^\s*\[([^\]]+)\]\s*(.*)$", ligne)
        if m:
            if courant:
                sections.append((courant, "\n".join(lignes).strip()))
            courant = sans_accents(m.group(1)).strip().upper()
            lignes = [m.group(2)] if m.group(2).strip() else []
        elif courant:
            lignes.append(ligne)
    if courant:
        sections.append((courant, "\n".join(lignes).strip()))
    return sections


def choisir_voix(valeur):
    v = sans_accents(valeur).lower()
    if "neural" in v:
        return valeur.strip()
    if "femme" in v or "vivienne" in v or "f" == v.strip():
        return VOIX_FEMME
    return VOIX_HOMME


def nom_fichier(titre):
    nom = re.sub(r'[<>:"/\\|?*\n\r\t]', "", titre).strip(" .")
    return nom[:120] or "priere"


async def generer(texte, voix, sortie):
    import edge_tts
    await edge_tts.Communicate(texte, voix, rate=VITESSE).save(str(sortie))


def traiter(fichier):
    sections = analyser(lire(fichier))
    titre = next((c for b, c in sections if b.startswith("TITRE")), "") or fichier.stem
    voix = choisir_voix(next((c for b, c in sections if b.startswith("VOIX")), ""))
    priere = next((c for b, c in sections if b.startswith("PRIERE")), "")
    shorts = [c for b, c in sections if b.startswith("SHORT") and c]

    base = nom_fichier(titre.splitlines()[0])
    print(f"   Titre : {base}")
    print(f"   Voix  : {voix}")

    if priere:
        mots = len(priere.split())
        sortie = DOSSIER_PRIERES / f"{base}.mp3"
        print(f"   -> Prière longue ({mots} mots, ~{mots // 145} min)... patience")
        asyncio.run(generer(priere, voix, sortie))
        print(f"      OK : {sortie}")
    else:
        print("   !! Aucune section [PRIERE] trouvée.")

    for i, texte in enumerate(shorts, 1):
        sortie = DOSSIER_SHORTS / f"{base} - short {i}.mp3"
        print(f"   -> Short {i} ({len(texte.split())} mots)...")
        asyncio.run(generer(texte, voix, sortie))
        print(f"      OK : {sortie}")

    DOSSIER_FAITS.mkdir(exist_ok=True)
    shutil.move(str(fichier), str(DOSSIER_FAITS / fichier.name))
    print(f"   Script déplacé dans : deja_generes\\")


def main():
    print("=" * 60)
    print("  GÉNÉRATION DES PRIÈRES — Radio Sources de Vie")
    print("=" * 60)

    try:
        import edge_tts  # noqa: F401
    except ImportError:
        print("\nERREUR : edge-tts n'est pas installé.")
        print("Tape dans la fenêtre :  py -m pip install edge-tts")
        return

    if not BASE.exists():
        print(f"\nERREUR : le disque/dossier est introuvable : {BASE}")
        return

    DOSSIER_SCRIPTS.mkdir(parents=True, exist_ok=True)
    DOSSIER_SHORTS.mkdir(parents=True, exist_ok=True)

    fichiers = sorted(DOSSIER_SCRIPTS.glob("*.txt"))
    if not fichiers:
        print(f"\nAucun fichier .txt trouvé dans :\n  {DOSSIER_SCRIPTS}")
        print("Dépose ton script (ex. rachel.txt) dans ce dossier et relance.")
        return

    print(f"\n{len(fichiers)} script(s) trouvé(s).\n")
    for f in fichiers:
        print(f"[{f.name}]")
        try:
            traiter(f)
        except Exception:
            print("   !! ERREUR sur ce fichier :")
            traceback.print_exc()
        print()

    print("Terminé.")


if __name__ == "__main__":
    main()
