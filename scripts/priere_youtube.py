 # -*- coding: utf-8 -*-
"""
Génère les audios des prières YouTube (Radio Sources de Vie) avec Edge TTS.
Version 2 : pauses, ton qui change selon le moment, musique douce en fond.

Format des fichiers .txt déposés dans "scripts_a_generer" :
    [TITRE]
    La prière de Rachel
    [VOIX]
    homme  (= Rémy)   /  henri  /  femme (= Vivienne)  /  ou un nom fr-FR-...Neural
    [PRIERE]
    ... texte de la prière longue (paragraphes séparés par une ligne vide) ...
    [SHORT]
    ... texte du short 1 ...
    [SHORT]
    ... (etc.)

Musique : mets un fichier "musique_fond.mp3" dans le dossier
"Prières qui ont changé une destinée" pour l'utiliser en fond.
Sinon, la prière est générée avec la voix seule.
"""
import asyncio
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
import unicodedata
import wave
from pathlib import Path

# ---------- Dossiers ----------
BASE = Path(r"D:\Audio pour Video shorts")
DOSSIER_PRIERES = BASE / "Prières qui ont changé une destinée"
DOSSIER_SCRIPTS = DOSSIER_PRIERES / "scripts_a_generer"
DOSSIER_FAITS = DOSSIER_SCRIPTS / "deja_generes"
DOSSIER_SHORTS = BASE / "Audio short"
MUSIQUE = DOSSIER_PRIERES / "musique_fond.mp3"

# ---------- Voix ----------
VOIX_HOMME = "fr-FR-RemyMultilingualNeural"
VOIX_HENRI = "fr-FR-HenriNeural"
VOIX_FEMME = "fr-FR-VivienneMultilingualNeural"

# ---------- Réglages par type de passage ----------
# vitesse, hauteur, volume, pause après (secondes)
STYLES = {
    "accroche":    dict(rate="-8%",  pitch="-2Hz", volume="+0%",  pause=1.8),
    "verset":      dict(rate="-15%", pitch="-3Hz", volume="+0%",  pause=2.2),
    "priere":      dict(rate="-12%", pitch="-4Hz", volume="+0%",  pause=1.4),
    "confession":  dict(rate="-18%", pitch="-6Hz", volume="-8%",  pause=1.8),
    "declaration": dict(rate="-2%",  pitch="+2Hz", volume="+12%", pause=0.9),
    "amen":        dict(rate="-20%", pitch="-5Hz", volume="+0%",  pause=2.5),
}
FACTEUR_PAUSE_SHORT = 0.6      # pauses plus courtes dans les shorts
VOLUME_MUSIQUE_FICHIER = 0.12  # volume de ta musique_fond.mp3
VOLUME_NAPPE = 0.55            # volume de la nappe générée
UTILISER_NAPPE = False         # False = pas de nappe générée (elle faisait un ronflement)
INTRO, OUTRO = 3.0, 4.0        # secondes de musique avant / après la voix
TAUX = 24000


# ================= Outils =================

def sans_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def assurer_paquets():
    for module, paquet in (("edge_tts", "edge-tts"), ("imageio_ffmpeg", "imageio-ffmpeg")):
        try:
            __import__(module)
        except ImportError:
            print(f"Installation de {paquet}...")
            subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", paquet], check=True)


def ffmpeg():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def lancer(args):
    r = subprocess.run([ffmpeg(), "-hide_banner", "-loglevel", "error", "-y"] + args,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())


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
    v = sans_accents(valeur).lower().strip()
    if "neural" in v:
        return valeur.strip()
    if "henri" in v:
        return VOIX_HENRI
    if "femme" in v or "vivienne" in v or v == "f":
        return VOIX_FEMME
    return VOIX_HOMME


def nom_fichier(titre):
    nom = re.sub(r'[<>:"/\\|?*\n\r\t]', "", titre).strip(" .")
    return nom[:120] or "priere"


# ================= Découpage en passages =================

DECL = re.compile(r"^\s*(au nom de j[eé]sus|par le sang de l.agneau)", re.I)


def est_verset(texte):
    t = texte.strip()
    if "«" not in t:
        return False
    avant = t.split("«", 1)[0].lower()
    return ("verset" in avant or "chapitre" in avant) and t.endswith("»")


def decouper_priere(texte):
    """Transforme la prière en liste de (style, texte)."""
    paragraphes = [p.strip() for p in re.split(r"\n\s*\n", texte) if p.strip()]
    segments = []
    premier_verset_vu = False
    for i, p in enumerate(paragraphes):
        lignes = [l.strip() for l in p.splitlines() if l.strip()]
        # Paragraphe de déclarations : une ligne = un passage
        if lignes and all(DECL.match(l) for l in lignes):
            for l in lignes:
                segments.append(("declaration", l))
            continue
        bloc = " ".join(lignes)
        if est_verset(bloc):
            premier_verset_vu = True
            segments.append(("verset", bloc))
        elif not premier_verset_vu:
            segments.append(("accroche", bloc))
        elif i == len(paragraphes) - 1 and "amen" in bloc.lower():
            segments.append(("amen", bloc))
        elif re.search(r"pardonne|confess", bloc, re.I):
            segments.append(("confession", bloc))
        elif any(DECL.match(l) for l in lignes):
            # paragraphe mixte : texte + déclarations
            for l in lignes:
                segments.append(("declaration" if DECL.match(l) else "priere", l))
        else:
            segments.append(("priere", bloc))
    return segments


def decouper_short(texte):
    segments = []
    for l in [l.strip() for l in texte.splitlines() if l.strip()]:
        if DECL.match(l):
            segments.append(("declaration", l))
        elif "«" in l or re.match(r"^(gen[eè]se|psaume|[eé]sa[iï]e|exode|j[eé]r[eé]mie|romains|proverbes|apocalypse|premi[eè]re)", l, re.I):
            segments.append(("verset", l))
        elif l.lower().startswith("abonne"):
            segments.append(("accroche", l))
        else:
            segments.append(("priere", l))
    return segments


# ================= Audio =================

async def _tts(texte, voix, style, fichier):
    import edge_tts
    s = STYLES[style]
    await edge_tts.Communicate(texte, voix, rate=s["rate"], pitch=s["pitch"],
                               volume=s["volume"]).save(str(fichier))


def tts(texte, voix, style, fichier):
    for essai in range(3):
        try:
            asyncio.run(_tts(texte, voix, style, fichier))
            if fichier.exists() and fichier.stat().st_size > 0:
                return
        except Exception:
            if essai == 2:
                raise
        time.sleep(2 + essai * 3)
    raise RuntimeError("Edge TTS n'a rien renvoyé")


def duree_wav(chemin):
    with wave.open(str(chemin)) as w:
        return w.getnframes() / w.getframerate()


def creer_silence(chemin, secondes):
    lancer(["-f", "lavfi", "-i", f"anullsrc=r={TAUX}:cl=mono", "-t", f"{secondes:.2f}",
            "-c:a", "pcm_s16le", str(chemin)])


def creer_nappe(chemin, secondes):
    expr = ("0.05*sin(2*PI*110*t)*(0.7+0.3*sin(2*PI*0.05*t))"
            "+0.045*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*0.08*t))"
            "+0.035*sin(2*PI*277.18*t)*(0.6+0.4*sin(2*PI*0.11*t))"
            "+0.035*sin(2*PI*329.63*t)*(0.6+0.4*sin(2*PI*0.07*t))"
            "+0.02*sin(2*PI*440*t)*(0.5+0.5*sin(2*PI*0.13*t))")
    lancer(["-f", "lavfi", "-i", f"aevalsrc={expr}:s={TAUX}:d={secondes:.1f}",
            "-af", "lowpass=f=900,aecho=0.8:0.6:120|250:0.35|0.25,volume=1.6",
            "-c:a", "pcm_s16le", str(chemin)])


def produire(segments, voix, sortie, facteur_pause=1.0, afficher=True):
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        morceaux = []
        n = len(segments)
        for i, (style, texte) in enumerate(segments):
            if afficher:
                print(f"\r      passage {i + 1}/{n} ", end="", flush=True)
            mp3, wav = tmp / f"s{i}.mp3", tmp / f"s{i}.wav"
            tts(texte, voix, style, mp3)
            lancer(["-i", str(mp3), "-ar", str(TAUX), "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
            morceaux.append(wav)
            pause = tmp / f"p{i}.wav"
            creer_silence(pause, STYLES[style]["pause"] * facteur_pause)
            morceaux.append(pause)
        if afficher:
            print()

        liste = tmp / "liste.txt"
        liste.write_text("".join(f"file '{m.as_posix()}'\n" for m in morceaux), encoding="utf-8")
        voix_wav = tmp / "voix.wav"
        lancer(["-f", "concat", "-safe", "0", "-i", str(liste), "-c:a", "pcm_s16le", str(voix_wav)])

        total = INTRO + duree_wav(voix_wav) + OUTRO
        if not MUSIQUE.exists() and not UTILISER_NAPPE:
            # Voix seule, propre (petit silence avant / après)
            lancer(["-i", str(voix_wav), "-af",
                    "adelay=800,apad=pad_dur=2,acompressor=threshold=0.5:ratio=2,alimiter=limit=0.95",
                    "-ac", "2", "-c:a", "libmp3lame", "-b:a", "160k", str(sortie)])
            return duree_wav(voix_wav) + 2.8
        if MUSIQUE.exists():
            entree = ["-stream_loop", "-1", "-i", str(MUSIQUE)]
            vol = VOLUME_MUSIQUE_FICHIER
        else:
            nappe = tmp / "nappe.wav"
            creer_nappe(nappe, total + 1)
            entree = ["-i", str(nappe)]
            vol = VOLUME_NAPPE

        filtre = (
            f"[0:a]adelay={int(INTRO * 1000)},apad=pad_dur={OUTRO}[v];"
            f"[1:a]aresample={TAUX},aformat=channel_layouts=mono,volume={vol},"
            f"afade=t=in:d=3,afade=t=out:st={max(total - 5, 0):.2f}:d=5[m];"
            f"[v][m]amix=inputs=2:duration=first:normalize=0,"
            f"acompressor=threshold=0.5:ratio=2,alimiter=limit=0.95[out]"
        )
        lancer(["-i", str(voix_wav)] + entree +
               ["-filter_complex", filtre, "-map", "[out]", "-t", f"{total:.2f}",
                "-ac", "2", "-c:a", "libmp3lame", "-b:a", "160k", str(sortie)])
        return total


# ================= Traitement =================

def traiter(fichier):
    sections = analyser(lire(fichier))
    titre = next((c for b, c in sections if b.startswith("TITRE")), "") or fichier.stem
    voix = choisir_voix(next((c for b, c in sections if b.startswith("VOIX")), ""))
    priere = next((c for b, c in sections if b.startswith("PRIERE")), "")
    shorts = [c for b, c in sections if b.startswith("SHORT") and c]

    base = nom_fichier(titre.splitlines()[0])
    print(f"   Titre : {base}")
    print(f"   Voix  : {voix}")
    print(f"   Musique : {'musique_fond.mp3' if MUSIQUE.exists() else ('nappe générée' if UTILISER_NAPPE else 'aucune (voix seule)')}")

    if priere:
        segs = decouper_priere(priere)
        mots = len(priere.split())
        print(f"   -> Prière longue ({mots} mots, {len(segs)} passages)... patience")
        sortie = DOSSIER_PRIERES / f"{base}.mp3"
        duree = produire(segs, voix, sortie)
        print(f"      OK ({int(duree // 60)} min {int(duree % 60)} s) : {sortie}")
    else:
        print("   !! Aucune section [PRIERE] trouvée.")

    for i, texte in enumerate(shorts, 1):
        sortie = DOSSIER_SHORTS / f"{base} - short {i}.mp3"
        print(f"   -> Short {i} ({len(texte.split())} mots)...")
        duree = produire(decouper_short(texte), voix, sortie, FACTEUR_PAUSE_SHORT, afficher=False)
        print(f"      OK ({int(duree)} s) : {sortie}")

    DOSSIER_FAITS.mkdir(exist_ok=True)
    shutil.move(str(fichier), str(DOSSIER_FAITS / fichier.name))
    print("   Script déplacé dans : deja_generes\\")


def main():
    print("=" * 60)
    print("  GÉNÉRATION DES PRIÈRES — Radio Sources de Vie (v2)")
    print("=" * 60)

    assurer_paquets()

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
            print("\n   !! ERREUR sur ce fichier :")
            traceback.print_exc()
        print()

    print("Terminé.")


if __name__ == "__main__":
    main()
