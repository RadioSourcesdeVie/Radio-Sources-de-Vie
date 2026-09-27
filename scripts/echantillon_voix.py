# -*- coding: utf-8 -*-
"""
Échantillons de voix "priante" — Radio Sources de Vie
Génère le même passage de la prière de Rachel avec 4 voix,
avec pauses, variations de ton et musique douce en fond.

Musique : si un fichier "musique_fond.mp3" se trouve dans le dossier
des échantillons, il est utilisé. Sinon, une nappe douce est créée.
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import traceback
import wave
from pathlib import Path

SORTIE = Path(r"D:\Audio pour Video shorts\Prières qui ont changé une destinée\echantillons_voix")

VOIX = [
    ("1 - Vivienne (voix actuelle)", "fr-FR-VivienneMultilingualNeural"),
    ("2 - Denise (France)", "fr-FR-DeniseNeural"),
    ("3 - Sylvie (Québec)", "fr-CA-SylvieNeural"),
    ("4 - Charline (Belgique)", "fr-BE-CharlineNeural"),
]

# Réglages par type de passage : vitesse, hauteur, volume, pause après (secondes)
STYLES = {
    "accroche":    dict(rate="-8%",  pitch="-2Hz", volume="+0%",  pause=1.8),
    "verset":      dict(rate="-16%", pitch="-3Hz", volume="+0%",  pause=2.2),
    "priere":      dict(rate="-12%", pitch="-4Hz", volume="+0%",  pause=1.4),
    "confession":  dict(rate="-20%", pitch="-7Hz", volume="-8%",  pause=1.8),
    "declaration": dict(rate="-2%",  pitch="+2Hz", volume="+12%", pause=0.9),
    "amen":        dict(rate="-22%", pitch="-6Hz", volume="+0%",  pause=2.5),
}

PASSAGE = [
    ("accroche", "Et si la jalousie qui te ronge, la comparaison qui t'épuise, l'attente qui te brise le cœur, étaient justement ce qui allait enfin te mettre à genoux devant Dieu ?"),
    ("accroche", "Ce soir, ne cache plus rien. Prie avec Rachel."),
    ("verset", "Genèse chapitre trente, verset premier : « Lorsque Rachel vit qu'elle ne donnait point d'enfants à Jacob, elle porta envie à sa sœur, et elle dit à Jacob : Donne-moi des enfants, ou je meurs ! »"),
    ("priere", "Seigneur... Je viens à Toi ce soir avec les mots de Rachel dans ma bouche. Des mots crus, sans détour. Elle n'a pas poli sa prière. Elle a crié ce qu'elle portait vraiment."),
    ("priere", "Tu connais les nuits où j'ai pleuré sans bruit, pour que personne n'entende. Tu connais la question que je n'ose plus poser à voix haute : Seigneur, et moi ? Quand est-ce que ce sera mon tour ?"),
    ("confession", "Je confesse l'envie. Je confesse les fois où j'ai regardé la bénédiction d'une autre femme, et où j'ai senti mon cœur se serrer au lieu de se réjouir. Pardonne-moi, Seigneur."),
    ("declaration", "Au nom de Jésus, je brise tout silence du ciel sur ma situation !"),
    ("declaration", "Par le sang de l'Agneau, je déclare que le temps de l'attente touche à sa fin !"),
    ("declaration", "Au nom de Jésus, je brise tout esprit de comparaison et de jalousie !"),
    ("declaration", "Par le sang de l'Agneau, je déclare que l'opprobre est enlevé !"),
    ("amen", "Souviens-Toi de moi, Seigneur, comme Tu T'es souvenu de Rachel. Amen."),
]

TAUX = 24000  # fréquence d'échantillonnage des voix Edge


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


async def generer_segment(texte, voix, style, fichier_mp3):
    import edge_tts
    s = STYLES[style]
    await edge_tts.Communicate(texte, voix, rate=s["rate"], pitch=s["pitch"],
                               volume=s["volume"]).save(str(fichier_mp3))


def duree_wav(chemin):
    with wave.open(str(chemin)) as w:
        return w.getnframes() / w.getframerate()


def creer_silence(chemin, secondes):
    lancer(["-f", "lavfi", "-i", f"anullsrc=r={TAUX}:cl=mono", "-t", f"{secondes}",
            "-c:a", "pcm_s16le", str(chemin)])


def creer_nappe(chemin, secondes):
    """Nappe douce (accord en la majeur qui respire lentement)."""
    expr = ("0.05*sin(2*PI*110*t)*(0.7+0.3*sin(2*PI*0.05*t))"
            "+0.045*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*0.08*t))"
            "+0.035*sin(2*PI*277.18*t)*(0.6+0.4*sin(2*PI*0.11*t))"
            "+0.035*sin(2*PI*329.63*t)*(0.6+0.4*sin(2*PI*0.07*t))"
            "+0.02*sin(2*PI*440*t)*(0.5+0.5*sin(2*PI*0.13*t))")
    lancer(["-f", "lavfi", "-i", f"aevalsrc={expr}:s={TAUX}:d={secondes}",
            "-af", "lowpass=f=900,aecho=0.8:0.6:120|250:0.35|0.25,volume=1.6",
            "-c:a", "pcm_s16le", str(chemin)])


def assembler(voix_nom, voix_id, dossier_tmp, musique):
    morceaux = []
    for i, (style, texte) in enumerate(PASSAGE):
        mp3 = dossier_tmp / f"seg_{i}.mp3"
        wav = dossier_tmp / f"seg_{i}.wav"
        asyncio.run(generer_segment(texte, voix_id, style, mp3))
        lancer(["-i", str(mp3), "-ar", str(TAUX), "-ac", "1", "-c:a", "pcm_s16le", str(wav)])
        morceaux.append(wav)
        pause = dossier_tmp / f"pause_{i}.wav"
        creer_silence(pause, STYLES[style]["pause"])
        morceaux.append(pause)

    liste = dossier_tmp / "liste.txt"
    liste.write_text("".join(f"file '{m.as_posix()}'\n" for m in morceaux), encoding="utf-8")
    voix_wav = dossier_tmp / "voix.wav"
    lancer(["-f", "concat", "-safe", "0", "-i", str(liste), "-c:a", "pcm_s16le", str(voix_wav)])

    intro, outro = 3.0, 4.0
    total = intro + duree_wav(voix_wav) + outro

    if musique:
        entree_musique = ["-stream_loop", "-1", "-i", str(musique)]
        vol_musique = "0.12"
    else:
        nappe = dossier_tmp / "nappe.wav"
        creer_nappe(nappe, total + 1)
        entree_musique = ["-i", str(nappe)]
        vol_musique = "0.55"

    sortie = SORTIE / f"{voix_nom}.mp3"
    filtre = (
        f"[0:a]adelay={int(intro*1000)},apad=pad_dur={outro}[v];"
        f"[1:a]aresample={TAUX},aformat=channel_layouts=mono,volume={vol_musique},"
        f"afade=t=in:d=3,afade=t=out:st={total-5}:d=5[m];"
        f"[v][m]amix=inputs=2:duration=first:normalize=0,"
        f"acompressor=threshold=0.5:ratio=2,alimiter=limit=0.95[out]"
    )
    lancer(["-i", str(voix_wav)] + entree_musique +
           ["-filter_complex", filtre, "-map", "[out]", "-t", f"{total}",
            "-ac", "2", "-c:a", "libmp3lame", "-b:a", "160k", str(sortie)])
    return sortie


def main():
    print("=" * 60)
    print("  ÉCHANTILLONS DE VOIX — Prière de Rachel")
    print("=" * 60)
    assurer_paquets()
    SORTIE.mkdir(parents=True, exist_ok=True)

    musique = SORTIE / "musique_fond.mp3"
    musique = musique if musique.exists() else None
    print("Musique de fond :", musique.name if musique else "nappe douce générée")
    print()

    for nom, voix_id in VOIX:
        print(f"-> {nom} ...")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                f = assembler(nom, voix_id, Path(tmp), musique)
            print(f"   OK : {f}")
        except Exception:
            print("   !! ERREUR :")
            traceback.print_exc()

    print("\nTerminé. Les échantillons sont dans :")
    print(f"  {SORTIE}")
    try:
        os.startfile(str(SORTIE))
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    finally:
        input("\nAppuie sur Entrée pour fermer...")
