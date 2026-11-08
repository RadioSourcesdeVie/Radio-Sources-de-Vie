#!/usr/bin/env python3
"""
test_style.py - La meme voix, avec differentes directions de jeu.
Montre a quel point la consigne de ton change le resultat.
Usage : python test_style.py
Sortie: dossier test_style/
"""
import os, json, base64, wave, time, urllib.request
from pathlib import Path

MODELE = "gemini-3.8-flash-tts"
OUT    = Path("test_style")
SR     = 24000

TEXTE_SERMON = ("Mes freres et soeurs, Dieu ne nous demande pas d'etre parfaits. "
                "Il nous demande d'etre honnetes devant lui. "
                "C'est la que commence la vraie liberte.")

TEXTE_PRIERE = ("Seigneur, nous deposons devant toi nos fardeaux de cette semaine. "
                "Tu connais chaque larme. Donne-nous ta paix.")

TEXTE_NEWS   = ("Bonsoir chers auditeurs. Voici le journal du soir "
                "sur Radio Sources de Vie, ce samedi sept novembre.")

# (fichier, voix, texte, consigne de jeu)
ESSAIS = [
    ("sermon_Rasalgethi_pasteur", "Rasalgethi", TEXTE_SERMON,
     "Parle comme un pasteur experimente en chaire : chaleureux, grave, "
     "sans precipitation, avec des pauses qui laissent respirer le sens."),
    ("sermon_Rasalgethi_intime", "Rasalgethi", TEXTE_SERMON,
     "Parle doucement, presque en confidence, comme a une seule personne "
     "assise en face de toi."),
    ("sermon_Algenib_pasteur", "Algenib", TEXTE_SERMON,
     "Parle comme un pasteur experimente en chaire : chaleureux, grave, "
     "sans precipitation, avec des pauses qui laissent respirer le sens."),
    ("sermon_Gacrux_pasteur", "Gacrux", TEXTE_SERMON,
     "Parle comme un pasteur experimente en chaire : chaleureux, grave, "
     "sans precipitation, avec des pauses qui laissent respirer le sens."),

    ("priere_Sulafat_recueilli", "Sulafat", TEXTE_PRIERE,
     "Parle avec recueillement, tres doucement, lentement, comme une priere "
     "murmuree dans une eglise vide."),
    ("priere_Achernar_recueilli", "Achernar", TEXTE_PRIERE,
     "Parle avec recueillement, tres doucement, lentement, comme une priere "
     "murmuree dans une eglise vide."),

    ("news_Charon_radio", "Charon", TEXTE_NEWS,
     "Parle comme un presentateur de radio professionnel : clair, pose, "
     "rythme soutenu mais naturel, ton chaleureux."),
    ("news_Erinome_radio", "Erinome", TEXTE_NEWS,
     "Parle comme une presentatrice de radio professionnelle : claire, posee, "
     "rythme soutenu mais naturel, ton chaleureux."),

    # Temoins sans consigne, pour comparer
    ("TEMOIN_sermon_Rasalgethi_sans_consigne", "Rasalgethi", TEXTE_SERMON, None),
    ("TEMOIN_priere_Sulafat_sans_consigne", "Sulafat", TEXTE_PRIERE, None),
]

def charger_env():
    p = Path(".env")
    if not p.exists():
        return
    for l in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        l = l.strip()
        if not l or l.startswith("#") or "=" not in l:
            continue
        if l.startswith("export "):
            l = l[7:].strip()
        k, _, v = l.partition("=")
        v = v.strip().strip('"').strip("'")
        if k.strip() and v:
            os.environ.setdefault(k.strip(), v)

def ecrire_wav(pcm, chemin):
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm)

def parle(cle, voix, texte, consigne, chemin):
    # La consigne de jeu precede le texte, separee par ':'
    contenu = f"{consigne}\n\n{texte}" if consigne else texte
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{MODELE}:generateContent?key={cle}")
    corps = {
        "contents": [{"parts": [{"text": contenu}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voix}}
            },
        },
    }
    donnees = json.dumps(corps).encode("utf-8")
    for essai in range(1, 5):
        try:
            req = urllib.request.Request(
                url, data=donnees, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            pcm = base64.b64decode(
                d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            ecrire_wav(pcm, chemin)
            return len(pcm) / (SR * 2)
        except Exception as e:
            if getattr(e, "code", None) == 429 and essai < 4:
                a = 20 * essai
                print(f"        quota atteint, pause {a}s...")
                time.sleep(a)
                continue
            raise

def main():
    charger_env()
    cle = os.environ.get("GEMINI_KEY", "")
    if not cle:
        raise SystemExit("GEMINI_KEY introuvable dans .env")
    OUT.mkdir(exist_ok=True)

    print(f"\n{len(ESSAIS)} echantillons avec direction de jeu\n")
    ok = 0
    for nom, voix, texte, consigne in ESSAIS:
        f = OUT / f"{nom}.wav"
        if f.exists() and f.stat().st_size > 20000:
            print(f"  --  {nom}  deja genere")
            ok += 1
            continue
        try:
            sec = parle(cle, voix, texte, consigne, f)
            etiquette = "SANS consigne" if consigne is None else "avec consigne"
            print(f"  OK  {nom:<42} {sec:5.1f}s  ({etiquette})")
            ok += 1
            time.sleep(6)
        except Exception as e:
            msg = str(e)
            if hasattr(e, "read"):
                try:
                    msg = e.read().decode()[:120]
                except Exception:
                    pass
            print(f"  ERR {nom:<42} : {msg[:110]}")

    print(f"\n{ok}/{len(ESSAIS)} dans le dossier  test_style/")
    print("Comparez surtout les fichiers TEMOIN_ (sans consigne) aux autres.")

if __name__ == "__main__":
    main()
