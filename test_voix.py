#!/usr/bin/env python3
"""
test_voix.py - Un echantillon par voix candidate, avec VOTRE contenu.
API v1beta (la seule ou vivent les modeles TTS).
Usage : python test_voix.py
Sortie: dossier test_voix/  -> fichiers .wav a double-cliquer
"""
import os, json, glob, base64, wave, time, urllib.request
from pathlib import Path

MODELE  = "gemini-3.8-flash-tts"
SECOURS = "gemini-3.8-flash-lite-tts"
OUT     = Path("test_voix")
SR      = 24000          # Gemini renvoie du PCM 24 kHz mono 16 bits

CANDIDATS = {
    "priere": [("Sulafat", "chaleureuse"), ("Achernar", "douce"),
               ("Vindemiatrix", "tendre")],
    "sermon": [("Rasalgethi", "posee"), ("Algenib", "grave"),
               ("Gacrux", "mature"), ("Alnilam", "ferme")],
    "nouvelles": [("Charon", "informative"), ("Erinome", "claire"),
                  ("Iapetus", "clair")],
    "temoignage": [("Achird", "amicale"), ("Zubenelgenubi", "naturelle")],
    "meteo": [("Kore", "ferme"), ("Zephyr", "lumineuse")],
}

REPLI = {
    "priere":     "Seigneur, nous venons devant toi ce matin le coeur ouvert. Tu connais nos combats et nos silences. Donne-nous la force de marcher dans ta lumiere aujourd'hui.",
    "sermon":     "Mes freres et soeurs, la Parole de Dieu nous enseigne que la foi sans les oeuvres est morte. Ce n'est pas une condamnation, c'est une invitation a vivre ce que nous croyons.",
    "nouvelles":  "Bonjour chers auditeurs, voici les nouvelles de ce matin sur Radio Sources de Vie. En Haiti, les autorites ont annonce de nouvelles mesures pour soutenir les familles.",
    "temoignage": "Pendant des annees j'ai cru que Dieu m'avait oublie. Et puis un matin, la paix est revenue. Je ne peux pas l'expliquer autrement que par sa grace.",
    "meteo":      "A Ottawa, quatre degres Celsius, ciel nuageux. A Port-au-Prince, trente et un degres, legere pluie. Que Dieu benisse votre journee.",
}

SOURCES = {
    "priere":     "content/prayers/matin_*.json",
    "sermon":     "content/sermons/*.json",
    "nouvelles":  "content/resumes/haiti_*.json",
    "temoignage": "content/testimonies/*.json",
}

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

def extrait(usage, n=300):
    motif = SOURCES.get(usage)
    if motif:
        f = sorted(glob.glob(motif))
        if f:
            try:
                d = json.loads(Path(f[-1]).read_text(encoding="utf-8"))
                t = d.get("content") or d.get("resume") or d.get("text") or ""
                t = " ".join(t.split())
                if len(t) > 80:
                    c = t[:n]
                    pt = c.rfind(".")
                    return c[:pt + 1] if pt > 100 else c
            except Exception:
                pass
    return REPLI[usage]

def ecrire_wav(pcm, chemin):
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm)

def parle(cle, modele, texte, voix, chemin):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{modele}:generateContent?key={cle}")
    corps = {
        "contents": [{"parts": [{"text": texte}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voix}}
            },
        },
    }
    donnees = json.dumps(corps).encode("utf-8")
    derniere = None
    for essai in range(1, 5):
        req = urllib.request.Request(
            url, data=donnees, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            pcm = base64.b64decode(
                d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
            ecrire_wav(pcm, chemin)
            return len(pcm) / (SR * 2)
        except Exception as e:
            derniere = e
            code = getattr(e, "code", None)
            if code == 429 and essai < 4:
                attente = 20 * essai
                print(f"        quota atteint, pause {attente}s puis reprise...")
                time.sleep(attente)
                continue
            raise
    raise derniere

def erreur_courte(e):
    if hasattr(e, "read"):
        try:
            return e.read().decode()[:120]
        except Exception:
            pass
    return str(e)[:120]

def main():
    charger_env()
    cle = os.environ.get("GEMINI_KEY", "")
    if not cle:
        raise SystemExit("GEMINI_KEY introuvable dans .env.\n"
                         "Ajoutez une ligne :  GEMINI_KEY=votre_cle")

    OUT.mkdir(exist_ok=True)
    sonde = OUT / "_essai.wav"
    modele = MODELE
    try:
        parle(cle, modele, "Test.", "Kore", sonde)
        print(f"\nModele : {modele}")
    except Exception as e:
        print(f"\n{modele} indisponible : {erreur_courte(e)[:70]}")
        modele = SECOURS
        print(f"Bascule sur : {modele}")
    sonde.unlink(missing_ok=True)

    total = 0
    for usage, voix_list in CANDIDATS.items():
        texte = extrait(usage)
        print(f"\n--- {usage.upper()} ---")
        print(f'    "{texte[:65]}..."')
        for nom, desc in voix_list:
            f = OUT / f"{usage}_{nom}.wav"
            if f.exists() and f.stat().st_size > 20000:
                print(f"    --  {nom:<14} deja genere")
                total += 1
                continue
            try:
                sec = parle(cle, modele, texte, nom, f)
                print(f"    OK  {nom:<14} ({desc:<12}) {sec:5.1f}s  {f.name}")
                total += 1
                time.sleep(6)
            except Exception as e:
                print(f"    ERR {nom:<14} : {erreur_courte(e)}")

    print(f"\n{total} echantillons dans le dossier  test_voix/")
    print("Double-cliquez les .wav pour les ecouter, puis dites-moi vos choix.")

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    main()
