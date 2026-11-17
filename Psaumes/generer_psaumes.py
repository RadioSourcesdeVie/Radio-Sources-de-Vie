# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Les 150 Psaumes en audio, avec la voix de Souvenan.
Utilise le meme moteur que la radio (rsdv_voix.py, Gemini 3.8 Flash TTS,
voix clonee) sans le modifier.

  py Psaumes\\generer_psaumes.py            -> genere tous les psaumes manquants
  py Psaumes\\generer_psaumes.py 1          -> genere seulement le Psaume 1
  py Psaumes\\generer_psaumes.py 1 23 150   -> genere ces psaumes-la

Textes  : Psaumes\\textes\\psaume_001.txt ...
Audio   : Psaumes\\audio\\Psaume_001.mp3 ...
Un psaume deja genere n'est jamais refait (supprimer le MP3 pour le refaire).
"""
import sys, time
from pathlib import Path

RADIO = Path(__file__).resolve().parent.parent      # dossier "Radio Sources De Vie"
sys.path.insert(0, str(RADIO))
import os; os.chdir(RADIO)                          # pour que rsdv_voix trouve le .env et ma_voix
import rsdv_voix

# Reglage propre aux Psaumes (ajoute en memoire, rsdv_voix.py n'est pas modifie)
rsdv_voix.VOIX["psaume"] = "MA_VOIX"
rsdv_voix.MA_VOIX_SECOURS["psaume"] = "Sulafat"
rsdv_voix.STYLES["psaume"] = "lecture biblique posee et solennelle, avec une courte pause entre chaque verset"

TEXTES = RADIO / "Psaumes" / "textes"
AUDIO  = RADIO / "Psaumes" / "audio"

def un_psaume(n):
    txt = TEXTES / f"psaume_{n:03d}.txt"
    mp3 = AUDIO / f"Psaume_{n:03d}.mp3"
    if not txt.exists():
        print(f"[--] Psaume {n} : texte absent ({txt.name})"); return
    if mp3.exists() and mp3.stat().st_size > 1000:
        print(f"[OK] Psaume {n} : deja fait"); return
    print(f"[..] Psaume {n} ...")
    moteur, ko, sec = rsdv_voix.parler(txt.read_text(encoding="utf-8"), "psaume", mp3, repli_gtts=False)
    print(f"     -> {mp3.name}  ({moteur}, {ko} Ko, {sec/60:.1f} min)")

if __name__ == "__main__":
    AUDIO.mkdir(parents=True, exist_ok=True)
    nums = [int(a) for a in sys.argv[1:]] or range(1, 151)
    for n in nums:
        try:
            un_psaume(n)
        except Exception as e:
            print(f"[XX] Psaume {n} : erreur -> {str(e)[:150]}")
        time.sleep(1)
    print("\nTermine. Les fichiers sont dans Psaumes\\audio")
