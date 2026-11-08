#!/usr/bin/env python3
"""
rsdv_voix.py - Module de synthese vocale Radio Sources de Vie.
Gemini TTS (v1beta) avec repli automatique sur gTTS.

Importe par generate_daily_audio.py et generate_resumes.py.
Ne se lance pas seul : python rsdv_voix.py pour un auto-test.
"""
import os, re, json, base64, wave, time, shutil, subprocess, array, urllib.request
try:
    import audioop          # present jusqu'a Python 3.12 : traitement rapide
except ImportError:
    audioop = None
from pathlib import Path

MODELE   = "gemini-3.8-flash-tts"
SECOURS  = "gemini-3.8-flash-lite-tts"
SR       = 24000          # Gemini renvoie du PCM 24 kHz mono 16 bits
MAX_CAR  = 3000           # taille max d'un morceau de texte
DEBIT    = 64             # kbps du MP3 (64 = taille des fichiers actuels)
PIC_CIBLE_DB = -3.0       # marge anti-saturation : le MP3 depasse l'original
PAUSE    = 6              # secondes entre deux appels (limite de debit)

# --- Voix par segment -------------------------------------------------
VOIX = {
    "priere_matin":     "Sulafat",      # chaleureuse, feminine
    "priere_soir":      "Sulafat",
    "sermon":           "Algenib",      # grave, masculine
    "temoignage_homme": "Achird",       # amicale, masculine
    "temoignage_femme": "Vindemiatrix", # tendre, feminine
    "meteo":            "Kore",         # ferme, nette
    # Les resumes ont deux presentateurs dans les textes generes :
    "resume_chretien":  "Erinome",      # Charline - feminine, claire
    "resume_haiti":     "Erinome",      # Charline
    "resume_monde":     "Iapetus",      # Antoine - masculine, clair
    "resume_sport":     "Iapetus",      # Antoine
}
VOIX_DEFAUT = "Iapetus"

# --- Chargement de la cle --------------------------------------------
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

def cle_gemini():
    charger_env()
    return os.environ.get("GEMINI_KEY", "")

# --- Preparation du texte --------------------------------------------
def nettoyer(texte):
    t = re.sub(r'\*\*(.*?)\*\*', r'\1', texte)
    t = re.sub(r'\*(.*?)\*', r'\1', t)
    t = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', t)
    t = re.sub(r'^#{1,6}\s*', '', t, flags=re.MULTILINE)
    t = t.replace('*', '').replace('#', '').replace('_', ' ')
    t = re.sub(r'(\d+):(\d+)-(\d+)', r'\1 verset \2 a \3', t)
    t = re.sub(r'(\d+):(\d+)', r'\1 verset \2', t)
    return t.strip()

def decouper(texte, maxi=MAX_CAR):
    """Decoupe aux fins de phrase, jamais au milieu d'un mot."""
    texte = texte.strip()
    if len(texte) <= maxi:
        return [texte]
    morceaux, courant = [], ""
    for phrase in re.split(r'(?<=[.!?])\s+', texte):
        if len(courant) + len(phrase) + 1 <= maxi:
            courant = f"{courant} {phrase}".strip()
        else:
            if courant:
                morceaux.append(courant)
            while len(phrase) > maxi:          # phrase geante : coupe nette
                morceaux.append(phrase[:maxi])
                phrase = phrase[maxi:]
            courant = phrase
    if courant:
        morceaux.append(courant)
    return morceaux


# --- Nettoyage du signal ---------------------------------------------
def _sans_entete(pcm):
    """Retire un eventuel entete RIFF et garantit un nombre pair d'octets."""
    if len(pcm) > 44 and pcm[:4] == b"RIFF":
        i = pcm.find(b"data")
        if i != -1:
            pcm = pcm[i + 8:]
    if len(pcm) % 2:
        pcm = pcm[:-1]
    return pcm


def _couper_parasite(pcm):
    """
    Gemini ajoute parfois une bouffee de parasites en fin de generation.
    On la reconnait a des sauts entre echantillons voisins impossibles
    pour de la parole. Balayage depuis la fin, coupe juste avant.
    """
    a = array.array("h")
    a.frombytes(pcm)
    n = len(a)
    if n < SR:
        return pcm

    corps = int(n * 0.75)
    sauts = sorted(abs(a[i] - a[i-1]) for i in range(1, corps))
    if not sauts:
        return pcm
    ref = sauts[int(len(sauts) * 0.999)]
    # Un saut de plus de 30 000 points est impossible pour de la parole.
    seuil = min(max(3 * ref, 30000), 40000)

    dernier = None
    for i in range(n - 1, corps, -1):
        if abs(a[i] - a[i-1]) > seuil:
            dernier = i
            break
    if dernier is None:
        return pcm

    limite = max(corps, dernier - int(SR * 0.30))
    debut = dernier
    for i in range(dernier, limite, -1):
        if abs(a[i] - a[i-1]) > seuil:
            debut = i

    coupe = max(0, debut - int(SR * 0.03))
    if (n - coupe) > SR:            # garde-fou : jamais plus d'une seconde
        return pcm
    print(f"        parasite de fin retire ({(n - coupe) / SR * 1000:.0f} ms)")
    return a[:coupe].tobytes()

def _silence(ms):
    return b"\x00\x00" * int(SR * ms / 1000)

def _fondu(pcm, ms_debut=8, ms_fin=45):
    """Fondu d'entree et de sortie : supprime les clics de coupure nette."""
    a = array.array("h")
    a.frombytes(pcm)
    n = len(a)
    if n == 0:
        return pcm
    nd = min(int(SR * ms_debut / 1000), n // 2)
    nf = min(int(SR * ms_fin / 1000), n // 2)
    for i in range(nd):
        a[i] = int(a[i] * i / nd)
    for i in range(nf):
        a[n - 1 - i] = int(a[n - 1 - i] * i / nf)
    return a.tobytes()


def _normaliser(pcm, cible_db=PIC_CIBLE_DB):
    """Ramene le pic a -3 dBFS. Sans cette marge, le MP3 sature a la lecture."""
    if not pcm:
        return pcm
    cible = 32767 * (10 ** (cible_db / 20.0))
    if audioop is not None:
        pic = audioop.max(pcm, 2)
        if pic == 0:
            return pcm
        return audioop.mul(pcm, 2, cible / pic)
    a = array.array("h")
    a.frombytes(pcm)
    pic = max((abs(x) for x in a), default=0)
    if pic == 0:
        return pcm
    g = cible / pic
    for i in range(len(a)):
        v = int(a[i] * g)
        a[i] = 32767 if v > 32767 else (-32768 if v < -32768 else v)
    return a.tobytes()

# --- Appel Gemini -----------------------------------------------------
def _appel(cle, modele, texte, voix):
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
    for essai in range(1, 6):
        try:
            req = urllib.request.Request(
                url, data=donnees, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=240) as r:
                d = json.loads(r.read())
            return base64.b64decode(
                d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])
        except Exception as e:
            code = getattr(e, "code", None)
            if code in (429, 500, 503) and essai < 5:
                attente = 15 * essai
                print(f"        debit limite ({code}), pause {attente}s...")
                time.sleep(attente)
                continue
            raise

def synthese(texte, voix):
    """Texte complet -> PCM brut. Leve une exception si Gemini echoue."""
    cle = cle_gemini()
    if not cle:
        raise RuntimeError("GEMINI_KEY absente de .env")
    morceaux = decouper(nettoyer(texte))
    bouts = []
    modele = MODELE
    for i, m in enumerate(morceaux, 1):
        if len(morceaux) > 1:
            print(f"        morceau {i}/{len(morceaux)} ({len(m)} car.)")
        try:
            brut = _appel(cle, modele, m, voix)
        except Exception:
            if modele == MODELE:
                print(f"        {MODELE} indisponible, bascule sur {SECOURS}")
                modele = SECOURS
                brut = _appel(cle, modele, m, voix)
            else:
                raise
        # Chaque morceau est nettoye et adouci a ses deux extremites,
        # sinon la jointure produit un clic.
        bouts.append(_fondu(_couper_parasite(_sans_entete(brut))))
        if i < len(morceaux):
            time.sleep(PAUSE)
    # 180 ms de blanc entre les morceaux : respiration naturelle, pas de clic
    pcm = _silence(180).join(bouts)
    # Normalisation globale, jamais morceau par morceau,
    # sinon le volume sauterait au milieu du sermon.
    pcm = _normaliser(pcm)
    # Un peu de blanc a la fin, pour que RadioDJ ne coupe pas sur la syllabe
    return pcm + _silence(250)

# --- Ecriture du fichier ---------------------------------------------
def _wav(pcm, chemin):
    with wave.open(str(chemin), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm)

def pcm_vers_mp3(pcm, chemin_mp3):
    """Essaie ffmpeg, puis lameenc, sinon ecrit un WAV a cote."""
    chemin_mp3 = Path(chemin_mp3)
    chemin_mp3.parent.mkdir(parents=True, exist_ok=True)

    ff = shutil.which("ffmpeg")
    if ff:
        p = subprocess.run(
            [ff, "-y", "-loglevel", "error", "-f", "s16le", "-ar", str(SR),
             "-ac", "1", "-i", "pipe:0", "-b:a", f"{DEBIT}k", str(chemin_mp3)],
            input=pcm, capture_output=True)
        if p.returncode == 0 and chemin_mp3.exists():
            return "ffmpeg"
        print(f"        ffmpeg a echoue : {p.stderr.decode()[:80]}")

    try:
        import lameenc
        enc = lameenc.Encoder()
        enc.set_bit_rate(DEBIT)
        enc.set_in_sample_rate(SR)
        enc.set_channels(1)
        enc.set_quality(3)
        data = enc.encode(pcm) + enc.flush()
        chemin_mp3.write_bytes(bytes(data))
        return "lameenc"
    except ImportError:
        pass
    except Exception as e:
        print(f"        lameenc a echoue : {str(e)[:80]}")

    wav = chemin_mp3.with_suffix(".wav")
    _wav(pcm, wav)
    print(f"        AUCUN encodeur MP3 : ecrit en WAV -> {wav.name}")
    print(f"        Pour avoir du MP3 :  pip install lameenc")
    return "wav"

# --- Point d'entree ---------------------------------------------------
def parler(texte, cle_voix, chemin_mp3, repli_gtts=True):
    """
    Genere chemin_mp3 a partir du texte.
    cle_voix : une cle de VOIX, ou directement un nom de voix Gemini.
    Retourne (moteur, taille_ko).
    """
    voix = VOIX.get(cle_voix, cle_voix if cle_voix in VOIX.values() else VOIX_DEFAUT)
    chemin_mp3 = Path(chemin_mp3)
    chemin_mp3.parent.mkdir(parents=True, exist_ok=True)

    try:
        pcm = synthese(texte, voix)
        encodeur = pcm_vers_mp3(pcm, chemin_mp3)
        cible = chemin_mp3 if encodeur != "wav" else chemin_mp3.with_suffix(".wav")
        secondes = len(pcm) / (SR * 2)
        return f"gemini/{voix}", cible.stat().st_size // 1024, secondes
    except Exception as e:
        print(f"        Gemini a echoue : {str(e)[:100]}")
        if not repli_gtts:
            raise
        print(f"        repli sur gTTS pour ne pas laisser de silence")
        from gtts import gTTS
        gTTS(text=nettoyer(texte), lang="fr", slow=False).save(str(chemin_mp3))
        return "gTTS", chemin_mp3.stat().st_size // 1024, 0.0

def voix_temoignage(data):
    """Choisit la voix selon le narrateur indique dans le JSON."""
    g = str(data.get("narrateur", "")).strip().lower()
    if g.startswith("f"):
        return "temoignage_femme"
    if g.startswith("h") or g.startswith("m"):
        return "temoignage_homme"
    texte = f"{data.get('title','')} {data.get('content','')}"[:400].lower()
    if re.search(r"\bje m'appelle\s+(marie|rose|jeanne|esther|ruth|sarah|claudine|nadege|myrlande|fabiola)", texte):
        return "temoignage_femme"
    return "temoignage_homme"

if __name__ == "__main__":
    print("Auto-test rsdv_voix")
    print(f"  cle Gemini : {'presente' if cle_gemini() else 'ABSENTE'}")
    print(f"  ffmpeg     : {shutil.which('ffmpeg') or 'absent'}")
    try:
        import lameenc; print("  lameenc    : present")
    except ImportError:
        print("  lameenc    : absent")
    t = "Ceci est un essai de la voix de Radio Sources de Vie."
    moteur, ko, sec = parler(t, "meteo", "test_module.mp3")
    produit = Path("test_module.mp3")
    if not produit.exists():
        produit = Path("test_module.wav")
    print(f"  resultat   : {moteur}, {ko} Ko, {sec:.1f}s -> {produit.name}")
