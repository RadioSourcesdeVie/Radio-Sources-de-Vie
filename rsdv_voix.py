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
    "priere_matin":     "MA_VOIX",      # voix clonee de Souvenan
    "priere_soir":      "MA_VOIX",
    "sermon":           "MA_VOIX",      # voix clonee de Souvenan
    "temoignage_homme": "Achird",       # amicale, masculine
    "temoignage_femme": "Vindemiatrix", # tendre, feminine
    "meteo":            "Kore",         # ferme, nette
    # Les resumes ont deux presentateurs dans les textes generes :
    "resume_chretien":  "Erinome",      # Charline - feminine, claire
    "resume_haiti":     "Erinome",      # Charline
    "resume_monde":     "Iapetus",      # Antoine - masculine, clair
    "resume_sport":     "Iapetus",      # Antoine
    # Journal du soir : meme duo de presentateurs
    "journal_charline": "Erinome",
    "journal_antoine":  "Iapetus",
}
VOIX_DEFAUT = "Iapetus"

# "MA_VOIX" est remplace par l'identifiant de la voix clonee,
# lu dans ma_voix/voice_id.txt. Si le fichier manque, on retombe
# sur la voix de secours indiquee ici.
MA_VOIX_SECOURS = {"priere_matin": "Sulafat", "priere_soir": "Sulafat",
                   "sermon": "Algenib"}

# Consigne de jeu par segment. Courte : Google deconseille de surcharger.
STYLES = {
    "priere_matin": "calme et recueilli, parlant lentement",
    "priere_soir":  "calme et recueilli, parlant lentement, voix basse",
    "sermon":       "pose et chaleureux, comme un pasteur en chaire",
}

def id_ma_voix():
    f = Path("ma_voix/voice_id.txt")
    if f.exists():
        v = f.read_text(encoding="utf-8").strip()
        if v:
            return v
    return None

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


# --- Dates en toutes lettres ------------------------------------------
_MOIS = ["", "janvier", "février", "mars", "avril", "mai", "juin",
         "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
_UNITES = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
           "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze",
           "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"]
_DIZAINES = {20: "vingt", 30: "trente", 40: "quarante", 50: "cinquante",
             60: "soixante"}

def _nombre_en_lettres(n):
    """Suffisant pour un jour (1-31) et une annee (2000-2099)."""
    if n < 20:
        return _UNITES[n]
    d, u = divmod(n, 10)
    base = _DIZAINES.get(d * 10)
    if base is None:
        return str(n)
    if u == 0:
        return base
    if u == 1:
        return f"{base} et un"
    return f"{base}-{_UNITES[u]}"

def _annee_en_lettres(a):
    if 2000 <= a <= 2099:
        reste = a - 2000
        if reste == 0:
            return "deux mille"
        return "deux mille " + _nombre_en_lettres(reste)
    return str(a)

def dates_en_lettres(texte):
    """2026-11-08 -> huit novembre deux mille vingt-six."""
    def iso(m):
        a, mo, j = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1 <= mo <= 12 and 1 <= j <= 31):
            return m.group(0)
        jour = "premier" if j == 1 else _nombre_en_lettres(j)
        return f"{jour} {_MOIS[mo]} {_annee_en_lettres(a)}"
    texte = re.sub(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", iso, texte)

    def fr(m):
        j, mo, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1 <= mo <= 12 and 1 <= j <= 31):
            return m.group(0)
        jour = "premier" if j == 1 else _nombre_en_lettres(j)
        return f"{jour} {_MOIS[mo]} {_annee_en_lettres(a)}"
    return re.sub(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", fr, texte)

# Etiquettes de plan : on les dit pas a l'antenne, mais on garde le titre.
_ETIQ_SEULE = re.compile(
    r"^\s*(introduction|conclusion|intro|préambule|preambule|"
    r"ouverture|exhortation finale|appel final)\s*[:.\-–—]?\s*$",
    re.IGNORECASE)
_ETIQ_TITRE = re.compile(
    r"^\s*(?:point|partie|section|chapitre)\s*(?:n[°o]\s*)?"
    r"(?:\d+|un|deux|trois|quatre|cinq|premier|première|premiere|"
    r"deuxième|deuxieme|troisième|troisieme|quatrième|quatrieme)\s*"
    r"[:.\-–—]\s*(.+?)\s*$",
    re.IGNORECASE)
_ETIQ_NUE = re.compile(
    r"^\s*(?:point|partie|section)\s*\d+\s*[:.\-–—]?\s*$",
    re.IGNORECASE)

def retirer_etiquettes(texte):
    """
    Enleve 'Introduction', 'CONCLUSION', 'POINT 2 :' etc.
    Conserve le titre qui suit : 'POINT 2 : La reconciliation...'
    devient 'La reconciliation...'.
    """
    sortie = []
    for ligne in texte.split("\n"):
        if _ETIQ_SEULE.match(ligne) or _ETIQ_NUE.match(ligne):
            continue
        m = _ETIQ_TITRE.match(ligne)
        sortie.append(m.group(1) if m else ligne)
    # pas plus d'une ligne vide d'affilee
    net, vide = [], False
    for l in sortie:
        if l.strip():
            net.append(l); vide = False
        elif not vide:
            net.append(""); vide = True
    return "\n".join(net).strip()

def nettoyer(texte):
    texte = dates_en_lettres(retirer_etiquettes(texte))
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

def _appel_sdk(cle, modele, texte, voix, style):
    """Voix clonee ou style de jeu : passe par l'API interactions."""
    from google import genai
    client = genai.Client(api_key=cle,
                          http_options={"api_version": "v1beta"})
    contenu = {"type": "text", "text": texte}
    if style:
        contenu["annotations"] = [{"type": "speech_metadata", "style": style}]
    for essai in range(1, 6):
        try:
            r = client.interactions.create(
                model=modele,
                input=[{"type": "user_input", "content": [contenu]}],
                response_format={"type": "audio"},
                generation_config={"speech_config": [{"voice": voix}]},
            )
            return base64.b64decode(r.output_audio.data)
        except Exception as e:
            msg = str(e)
            if ("429" in msg or "503" in msg or "500" in msg) and essai < 5:
                attente = 15 * essai
                print(f"        debit limite, pause {attente}s...")
                time.sleep(attente)
                continue
            raise

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

def synthese(texte, voix, style=None):
    """Texte complet -> PCM brut. Leve une exception si Gemini echoue."""
    cle = cle_gemini()
    if not cle:
        raise RuntimeError("GEMINI_KEY absente de .env")
    clonee = voix.startswith(("voice_", "voicekey_"))
    if clonee or style:
        texte = texte.replace("\n\n", "\n\n<short pause>\n\n")
    morceaux = decouper(nettoyer(texte))
    bouts = []
    modele = MODELE
    for i, m in enumerate(morceaux, 1):
        if len(morceaux) > 1:
            print(f"        morceau {i}/{len(morceaux)} ({len(m)} car.)")
        appel = _appel_sdk if (clonee or style) else _appel
        args = (cle, modele, m, voix, style) if (clonee or style) else (cle, modele, m, voix)
        try:
            brut = appel(*args)
        except Exception:
            if modele == MODELE:
                print(f"        {MODELE} indisponible, bascule sur {SECOURS}")
                modele = SECOURS
                args = (cle, modele, m, voix, style) if (clonee or style) else (cle, modele, m, voix)
                brut = appel(*args)
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
    if voix == "MA_VOIX":
        voix = id_ma_voix() or MA_VOIX_SECOURS.get(cle_voix, VOIX_DEFAUT)
        if not voix.startswith("voice"):
            print(f"        voix clonee introuvable, repli sur {voix}")
    style = STYLES.get(cle_voix)
    chemin_mp3 = Path(chemin_mp3)
    chemin_mp3.parent.mkdir(parents=True, exist_ok=True)

    try:
        pcm = synthese(texte, voix, style)
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


def parler_duo(segments, chemin_mp3, repli_gtts=True):
    """
    Plusieurs voix dans un meme fichier (journal du soir co-presente).
    segments : liste de (texte, cle_voix).
    Tout est normalise d'un bloc a la fin, pour un volume homogene.
    """
    chemin_mp3 = Path(chemin_mp3)
    chemin_mp3.parent.mkdir(parents=True, exist_ok=True)
    try:
        bouts = []
        for i, (texte, cle_voix) in enumerate(segments, 1):
            if not texte or not texte.strip():
                continue
            voix = VOIX.get(cle_voix, VOIX_DEFAUT)
            if voix == "MA_VOIX":
                voix = id_ma_voix() or MA_VOIX_SECOURS.get(cle_voix, VOIX_DEFAUT)
            print(f"      segment {i}/{len(segments)} ({voix})")
            bouts.append(synthese(texte, voix, STYLES.get(cle_voix)))
            if i < len(segments):
                time.sleep(PAUSE)
        if not bouts:
            raise RuntimeError("aucun segment a lire")
        pcm = _normaliser(_silence(300).join(bouts)) + _silence(250)
        encodeur = pcm_vers_mp3(pcm, chemin_mp3)
        cible = chemin_mp3 if encodeur != "wav" else chemin_mp3.with_suffix(".wav")
        return "gemini/duo", cible.stat().st_size // 1024, len(pcm) / (SR * 2)
    except Exception as e:
        print(f"        Gemini a echoue : {str(e)[:100]}")
        if not repli_gtts:
            raise
        print("        repli sur gTTS")
        from gtts import gTTS
        tout = "\n\n".join(t for t, _ in segments if t and t.strip())
        gTTS(text=nettoyer(tout), lang="fr", slow=False).save(str(chemin_mp3))
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
