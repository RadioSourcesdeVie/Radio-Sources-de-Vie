#!/usr/bin/env python3
"""
enregistrer_voix.py - Enregistre les 2 extraits necessaires au clonage.
Produit directement du WAV 24000 Hz mono 16 bits dans ma_voix/.

Prerequis :  pip install sounddevice
Usage     :  python enregistrer_voix.py
"""
import sys, time, wave, array
from pathlib import Path

SR      = 24000
DOSSIER = Path("ma_voix")
REF     = DOSSIER / "reference.wav"
CONSENT = DOSSIER / "consentement.wav"

PHRASE = ("Je suis le proprietaire de cette voix et j'autorise Google "
          "a utiliser cette voix pour creer un modele de voix synthetique.")

PHRASE_ACCENTS = ("Je suis le propriétaire de cette voix et j'autorise Google "
                  "à utiliser cette voix pour créer un modèle de voix synthétique.")

def verifier_module():
    try:
        import sounddevice  # noqa
        return True
    except Exception:
        print("\nIl manque un module pour enregistrer. Tapez :")
        print("    pip install sounddevice")
        print("puis relancez ce script.\n")
        return False

def choisir_micro(sd):
    print("\n--- Microphones disponibles ---")
    entrees = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            entrees.append(i)
            defaut = " (par defaut)" if i == sd.default.device[0] else ""
            print(f"  [{i}] {d['name']}{defaut}")
    rep = input("\nNumero du micro (Entree = celui par defaut) : ").strip()
    if not rep:
        return None
    try:
        n = int(rep)
        return n if n in entrees else None
    except ValueError:
        return None

def niveau(a):
    pic = max((abs(x) for x in a), default=0)
    return pic / 32768.0

def barre(v, largeur=40):
    n = int(v * largeur)
    return "[" + "#" * n + "-" * (largeur - n) + "]"

def enregistrer(sd, secondes, micro):
    """Flux brut : aucun besoin de numpy, et vumetre en direct."""
    print(f"\n  Enregistrement de {secondes} s...")
    for i in (3, 2, 1):
        print(f"    {i}...")
        time.sleep(1)
    print("    >>> PARLEZ MAINTENANT <<<\n")

    bloc = 1200                      # 50 ms
    morceaux = []
    debut = time.time()
    with sd.RawInputStream(samplerate=SR, channels=1, dtype="int16",
                           blocksize=bloc, device=micro) as flux:
        while True:
            reste = secondes - (time.time() - debut)
            if reste <= 0:
                break
            donnees, _ = flux.read(bloc)
            b = bytes(donnees)
            morceaux.append(b)
            bl = array.array("h"); bl.frombytes(b)
            v = max((abs(x) for x in bl), default=0) / 32768.0
            print(f"    {reste:4.1f} s  {barre(v)} {v*100:3.0f}%   ", end="\r")
    print("    termine.                                              ")
    a = array.array("h")
    a.frombytes(b"".join(morceaux))
    return a

def rogner_silence(a, seuil=0.02, marge_ms=300):
    """Enleve le blanc au debut et a la fin."""
    s = int(32768 * seuil)
    d = 0
    while d < len(a) and abs(a[d]) < s:
        d += 1
    f = len(a) - 1
    while f > d and abs(a[f]) < s:
        f -= 1
    if f <= d:
        return a
    m = int(SR * marge_ms / 1000)
    return a[max(0, d - m): min(len(a), f + m)]

def ecrire(a, chemin):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(a.tobytes())

def controler(a, nom, mini, maxi):
    duree = len(a) / SR
    v = niveau(a)
    print(f"    {nom} : {duree:.1f} s   niveau {barre(v)} {v*100:.0f}%")
    souci = []
    if duree < mini:
        souci.append(f"trop court (minimum {mini} s)")
    if duree > maxi:
        souci.append(f"trop long (maximum {maxi} s)")
    if v < 0.25:
        souci.append("son trop faible : rapprochez-vous du micro et parlez plus fort")
    if v > 0.97:
        souci.append("son sature : eloignez-vous ou baissez le gain")
    for s in souci:
        print(f"      ATTENTION : {s}")
    return not souci

def main():
    if not verifier_module():
        return
    import sounddevice as sd

    quoi = sys.argv[1].lower() if len(sys.argv) > 1 else "tout"
    faire_ref = quoi in ("tout", "reference")
    faire_con = quoi in ("tout", "consentement")

    print("=" * 62)
    print("  CLONAGE DE VOIX - enregistrement des deux extraits")
    print("=" * 62)
    print("""
  Avant de commencer :
    - une piece silencieuse, sans ventilateur ni television
    - le meme micro pour les DEUX extraits, sans y toucher entre
    - parlez a distance constante, voix naturelle de predication
""")
    micro = choisir_micro(sd)
    ok1 = ok2 = True

    # --- Extrait 1 : reference ---
    if faire_ref:
        print("\n" + "-" * 62)
        print("  VOTRE VOIX (20 secondes)")
        print("-" * 62)
        print("""
  Lisez un passage biblique, ou parlez comme en chaire.
  Exemple : Psaume 23, ou quelques phrases de votre derniere predication.
  Parlez sans interruption pendant les 20 secondes.
""")
        input("  Appuyez sur Entree quand vous etes pret...")
        a1 = rogner_silence(enregistrer(sd, 20, micro))
        ok1 = controler(a1, "reference  ", 10, 30)
        ecrire(a1, REF)

    # --- Extrait 2 : consentement ---
    if faire_con:
        print("\n" + "-" * 62)
        print("  PHRASE DE CONSENTEMENT (15 secondes)")
        print("-" * 62)
        print("""
  IMPORTANT : Google transcrit cette phrase et la compare mot pour mot.
    - meme distance du micro que pour votre voix
    - parlez FORT et distinctement, sans vous presser
    - ne changez aucun mot, n'en ajoutez aucun
    - visez au moins 40% sur la barre de niveau
""")
        print("  Lisez exactement ceci :\n")
        print(f"      \"{PHRASE_ACCENTS}\"\n")
        input("  Appuyez sur Entree quand vous etes pret...")
        a2 = rogner_silence(enregistrer(sd, 15, micro))
        ok2 = controler(a2, "consentement", 3, 30)
        ecrire(a2, CONSENT)
    print(f"\n  Fichiers :\n    {REF}\n    {CONSENT}")
    print("\n  Reecoutez-les avant d'aller plus loin :")
    print(f"    start {REF}")
    print(f"    start {CONSENT}")
    if ok1 and ok2:
        print("\n  Tout est conforme. Etape suivante :")
        print("    python cloner_ma_voix.py")
    else:
        print("\n  Corrigez les points signales puis relancez ce script.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage :")
        print("  python enregistrer_voix.py                 les deux extraits")
        print("  python enregistrer_voix.py consentement    seulement le consentement")
        print("  python enregistrer_voix.py reference       seulement votre voix")
    else:
        main()
