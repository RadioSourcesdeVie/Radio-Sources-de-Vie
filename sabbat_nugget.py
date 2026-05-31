import os
import re
import sys
import requests
from dotenv import load_dotenv
load_dotenv()
# Support ANTHROPIC_KEY ou ANTHROPIC_API_KEY
if not os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_KEY")
from pathlib import Path
from datetime import datetime, date
from anthropic import Anthropic

SABBAT_DIR = Path("audio/sabbat")
SABBAT_DIR.mkdir(parents=True, exist_ok=True)

# ── URL du PDF par trimestre ──────────────────────────────────────────
PDF_TRIMESTRES = {
    "2026-2": "https://troisanges.com/EDS/2026-2/EDS2026-2M.pdf",
    # Ajoutez les prochains trimestres ici
}

def get_trimestre():
    """Retourne la clé trimestre selon la date du jour"""
    m = datetime.now().month
    if m <= 3:   return f"{datetime.now().year}-1"
    elif m <= 6: return f"{datetime.now().year}-2"
    elif m <= 9: return f"{datetime.now().year}-3"
    else:        return f"{datetime.now().year}-4"

def get_lecon_numero():
    """Calcule le numéro de leçon selon la semaine du trimestre"""
    today = date.today()
    m = today.month
    # Début du trimestre 2 = 28 mars 2026
    if m >= 4 and m <= 6:
        debut = date(2026, 3, 28)
        semaines = (today - debut).days // 7
        return min(max(semaines + 1, 1), 13)
    return 10  # défaut

def get_jour_semaine():
    """Retourne le nom du jour pour la leçon"""
    jours = {
        6: "Sabbat",      # samedi
        0: "Dimanche",
        1: "Lundi",
        2: "Mardi",
        3: "Mercredi",
        4: "Jeudi",
        5: "Vendredi"
    }
    return jours[datetime.now().weekday()]

def telecharger_pdf():
    """Télécharge le PDF du trimestre actuel"""
    cle = get_trimestre()
    url = PDF_TRIMESTRES.get(cle)
    if not url:
        print(f"[!] Pas de PDF configuré pour {cle}")
        return None
    cache = Path(f"content/sabbat/eds_{cle}.pdf")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        print(f"[OK] PDF en cache: {cache}")
        return str(cache)
    print(f"[...] Téléchargement PDF {cle}...")
    r = requests.get(url, timeout=30)
    if r.status_code == 200:
        cache.write_bytes(r.content)
        print(f"[OK] PDF sauvegardé: {cache}")
        return str(cache)
    print(f"[!] Erreur téléchargement: {r.status_code}")
    return None

def extraire_texte_pdf(pdf_path):
    """Extrait le texte du PDF"""
    try:
        import pdfplumber
        texte = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texte += t + "\n"
        return texte
    except ImportError:
        print("[!] Installation pdfplumber...")
        os.system("pip install pdfplumber --break-system-packages -q")
        import pdfplumber
        texte = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texte += t + "\n"
        return texte

def extraire_lecon_du_jour(texte_pdf):
    """Extrait la section de la leçon et du jour actuel"""
    lecon_num = get_lecon_numero()
    jour = get_jour_semaine()
    today = date.today()
    date_str = str(today.day)  # ex: "31"
    
    # Chercher la leçon dans le texte
    patterns = [
        f"Leçon {lecon_num}",
        f"Lecon {lecon_num}",
        f"LEÇON {lecon_num}",
    ]
    
    debut_lecon = -1
    for p in patterns:
        idx = texte_pdf.find(p)
        if idx > 0:
            debut_lecon = idx
            break
    
    if debut_lecon < 0:
        # Chercher par page approximative (leçon 10 = page ~124)
        idx = texte_pdf.find("La repentance et le pardon")
        if idx > 0:
            debut_lecon = idx
        else:
            return texte_pdf[:3000], "Leçon du jour"
    
    # Extraire ~4000 chars à partir du début de la leçon
    extrait = texte_pdf[debut_lecon:debut_lecon+5000]
    
    # Chercher "repentance et le pardon" d'abord dans l'extrait
    idx_rep = extrait.find("repentance")
    if idx_rep > 0:
        extrait = extrait[max(0,idx_rep-200):]

    # Chercher le jour spécifique
    jour_patterns = [jour, jour.upper(), jour.lower()]
    for jp in jour_patterns:
        idx = extrait.find(jp)
        if idx > 0:
            # Prendre 1500 chars autour du jour
            debut = max(0, idx - 100)
            extrait_jour = extrait[debut:debut+1500]
            return extrait_jour, f"Leçon {lecon_num} — {jour}"
    
    # Si jour pas trouvé, retourner intro de la leçon
    return extrait[:2000], f"Leçon {lecon_num}"

def generate_sabbat_text():
    """Génère le Sabbat Nugget basé sur la vraie leçon du jour"""
    client = Anthropic()
    
    jour = get_jour_semaine()
    lecon_num = get_lecon_numero()
    today = date.today().strftime("%d %B %Y")
    
    # Essayer de charger le PDF
    contenu_lecon = ""
    titre_lecon = f"Leçon {lecon_num}"
    
    pdf_path = telecharger_pdf()
    if pdf_path:
        try:
            contenu_lecon, titre_lecon = extraire_lecon_du_jour(pdf_path)
            print(f"[OK] Leçon extraite: {titre_lecon}")
        except Exception as e:
            print(f"[!] Erreur extraction: {e}")
    
    if contenu_lecon:
        prompt = f"""Tu es un pasteur adventiste qui présente le Sabbat School Nugget du jour pour Radio Sources de Vie.

LEÇON DU JOUR — {titre_lecon} ({today})
Jour: {jour}

CONTENU DE LA LEÇON (extrait du Guide Adulte officiel):
{contenu_lecon}

Génère un Sabbat School Nugget de 2 minutes basé EXACTEMENT sur ce contenu.

Format:
- Ouverture inspirante mentionnant le titre exact de la leçon du jour
- Verset biblique clé tiré de la leçon
- Résumé fidèle de l'enseignement principal du jour
- Application pratique concrète pour aujourd'hui
- Prière courte de clôture

Ton: sage, chaleureux, inspirant
Langue: Français
Public: Communauté chrétienne haïtienne
Important: Sois fidèle au contenu exact de la leçon, pas générique"""
    else:
        prompt = f"""Génère un Sabbat School Nugget pour {jour} {today}, Leçon {lecon_num} du trimestre adventiste sur "Grandir dans sa relation avec Dieu".

Format:
- Ouverture inspirante
- Verset biblique clé
- Leçon principale (3-4 phrases)
- Application pratique
- Prière courte

Ton: sage, chaleureux, inspirant. Langue: Français."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text, titre_lecon

def generate_audio(text, filename):
    """Génère l'audio avec ElevenLabs"""
    api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_KEY", "")
    if not api_key:
        print("[!] ELEVENLABS_API_KEY manquant")
        return False
    try:
        import requests as req
        voice_id = "onwK4e9ZLuTAKqWW03F9"  # Daniel - sage
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.7, "similarity_boost": 0.8}
        }
        r = req.post(url, json=data, headers=headers)
        if r.status_code == 200:
            Path(filename).write_bytes(r.content)
            return True
        print(f"[!] ElevenLabs erreur: {r.status_code}")
        return False
    except Exception as e:
        print(f"[!] Audio erreur: {e}")
        return False

def run():
    print("""
╔══════════════════════════════════════════════╗
║   SABBAT SCHOOL NUGGET — LEÇON DU JOUR      ║
╚══════════════════════════════════════════════╝
    """)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = date.today().isoformat()
    
    print("[1/3] Extraction de la leçon du jour...")
    text, theme = generate_sabbat_text()
    print(f"[OK] Thème: {theme}")
    
    print("[2/3] Sauvegarde du texte...")
    txt_file = SABBAT_DIR / f"{date_str}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(f"SABBAT SCHOOL NUGGET\n")
        f.write(f"Date: {date_str}\n")
        f.write(f"Thème: {theme}\n")
        f.write("="*50 + "\n\n")
        f.write(text)
    print(f"[OK] Texte: {txt_file.name}")
    
    print("[3/3] Génération audio...")
    mp3_file = SABBAT_DIR / f"{date_str}.mp3"
    success = generate_audio(text, str(mp3_file))
    if success:
        print(f"[OK] Audio: {mp3_file.name}")
    
    print(f"\n✅ Sabbat Nugget généré!\n   📅 {date_str}\n   📖 {theme}\n")

if __name__ == "__main__":
    run()

def extraire_lecon_du_jour(pdf_path_direct=None):
    """Extrait la section exacte du jour — index directs par leçon"""
    import pdfplumber
    lecon_num = get_lecon_numero()
    jour = get_jour_semaine()

    # Index de page pour chaque jour de chaque leçon
    # Leçon 1 commence index 5, chaque leçon = 13 pages
    base = 5 + (lecon_num - 1) * 13
    jour_index = {
        "Sabbat":   base,
        "Dimanche": base + 1,
        "Lundi":    base + 2,
        "Mardi":    base + 3,
        "Mercredi": base + 4,
        "Jeudi":    base + 5,
        "Vendredi": base + 6,
    }

    page_idx = jour_index.get(jour, base)
    pdf_file = pdf_path_direct or f"content/sabbat/eds_{get_trimestre()}.pdf"

    try:
        with pdfplumber.open(pdf_file) as pdf:
            if page_idx < len(pdf.pages):
                t = pdf.pages[page_idx].extract_text() or ""
                if t:
                    return t[:2000], f"Leçon {lecon_num} — {jour}"
    except Exception as e:
        print(f"[!] Erreur PDF: {e}")

    return "", f"Leçon {lecon_num}"ort requests
from dotenv import load_dotenv
load_dotenv()
# Support ANTHROPIC_KEY ou ANTHROPIC_API_KEY
if not os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_KEY"):
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_KEY")
from pathlib import Path
from datetime import datetime, date
from anthropic import Anthropic

SABBAT_DIR = Path("audio/sabbat")
SABBAT_DIR.mkdir(parents=True, exist_ok=True)

# ── URL du PDF par trimestre ──────────────────────────────────────────
PDF_TRIMESTRES = {
    "2026-2": "https://troisanges.com/EDS/2026-2/EDS2026-2M.pdf",
    # Ajoutez les prochains trimestres ici
}

def get_trimestre():
    """Retourne la clé trimestre selon la date du jour"""
    m = datetime.now().month
    if m <= 3:   return f"{datetime.now().year}-1"
    elif m <= 6: return f"{datetime.now().year}-2"
    elif m <= 9: return f"{datetime.now().year}-3"
    else:        return f"{datetime.now().year}-4"

def get_lecon_numero():
    """Calcule le numéro de leçon selon la semaine du trimestre"""
    today = date.today()
    m = today.month
    # Début du trimestre 2 = 28 mars 2026
    if m >= 4 and m <= 6:
        debut = date(2026, 3, 28)
        semaines = (today - debut).days // 7
        return min(max(semaines + 1, 1), 13)
    return 10  # défaut

def get_jour_semaine():
    """Retourne le nom du jour pour la leçon"""
    jours = {
        6: "Sabbat",      # samedi
        0: "Dimanche",
        1: "Lundi",
        2: "Mardi",
        3: "Mercredi",
        4: "Jeudi",
        5: "Vendredi"
    }
    return jours[datetime.now().weekday()]

def telecharger_pdf():
    """Télécharge le PDF du trimestre actuel"""
    cle = get_trimestre()
    url = PDF_TRIMESTRES.get(cle)
    if not url:
        print(f"[!] Pas de PDF configuré pour {cle}")
        return None
    cache = Path(f"content/sabbat/eds_{cle}.pdf")
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.exists():
        print(f"[OK] PDF en cache: {cache}")
        return str(cache)
    print(f"[...] Téléchargement PDF {cle}...")
    r = requests.get(url, timeout=30)
    if r.status_code == 200:
        cache.write_bytes(r.content)
        print(f"[OK] PDF sauvegardé: {cache}")
        return str(cache)
    print(f"[!] Erreur téléchargement: {r.status_code}")
    return None

def extraire_texte_pdf(pdf_path):
    """Extrait le texte du PDF"""
    try:
        import pdfplumber
        texte = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texte += t + "\n"
        return texte
    except ImportError:
        print("[!] Installation pdfplumber...")
        os.system("pip install pdfplumber --break-system-packages -q")
        import pdfplumber
        texte = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texte += t + "\n"
        return texte

def extraire_lecon_du_jour(texte_pdf):
    """Extrait la section de la leçon et du jour actuel"""
    lecon_num = get_lecon_numero()
    jour = get_jour_semaine()
    today = date.today()
    date_str = str(today.day)  # ex: "31"
    
    # Chercher la leçon dans le texte
    patterns = [
        f"Leçon {lecon_num}",
        f"Lecon {lecon_num}",
        f"LEÇON {lecon_num}",
    ]
    
    debut_lecon = -1
    for p in patterns:
        idx = texte_pdf.find(p)
        if idx > 0:
            debut_lecon = idx
            break
    
    if debut_lecon < 0:
        # Chercher par page approximative (leçon 10 = page ~124)
        idx = texte_pdf.find("La repentance et le pardon")
        if idx > 0:
            debut_lecon = idx
        else:
            return texte_pdf[:3000], "Leçon du jour"
    
    # Extraire ~4000 chars à partir du début de la leçon
    extrait = texte_pdf[debut_lecon:debut_lecon+5000]
    
    # Chercher "repentance et le pardon" d'abord dans l'extrait
    idx_rep = extrait.find("repentance")
    if idx_rep > 0:
        extrait = extrait[max(0,idx_rep-200):]

    # Chercher le jour spécifique
    jour_patterns = [jour, jour.upper(), jour.lower()]
    for jp in jour_patterns:
        idx = extrait.find(jp)
        if idx > 0:
            # Prendre 1500 chars autour du jour
            debut = max(0, idx - 100)
            extrait_jour = extrait[debut:debut+1500]
            return extrait_jour, f"Leçon {lecon_num} — {jour}"
    
    # Si jour pas trouvé, retourner intro de la leçon
    return extrait[:2000], f"Leçon {lecon_num}"

def generate_sabbat_text():
    """Génère le Sabbat Nugget basé sur la vraie leçon du jour"""
    client = Anthropic()
    
    jour = get_jour_semaine()
    lecon_num = get_lecon_numero()
    today = date.today().strftime("%d %B %Y")
    
    # Essayer de charger le PDF
    contenu_lecon = ""
    titre_lecon = f"Leçon {lecon_num}"
    
    pdf_path = telecharger_pdf()
    if pdf_path:
        try:
            contenu_lecon, titre_lecon = extraire_lecon_du_jour(pdf_path)
            print(f"[OK] Leçon extraite: {titre_lecon}")
        except Exception as e:
            print(f"[!] Erreur extraction: {e}")
    
    if contenu_lecon:
        prompt = f"""Tu es un pasteur adventiste qui présente le Sabbat School Nugget du jour pour Radio Sources de Vie.

LEÇON DU JOUR — {titre_lecon} ({today})
Jour: {jour}

CONTENU DE LA LEÇON (extrait du Guide Adulte officiel):
{contenu_lecon}

Génère un Sabbat School Nugget de 2 minutes basé EXACTEMENT sur ce contenu.

Format:
- Ouverture inspirante mentionnant le titre exact de la leçon du jour
- Verset biblique clé tiré de la leçon
- Résumé fidèle de l'enseignement principal du jour
- Application pratique concrète pour aujourd'hui
- Prière courte de clôture

Ton: sage, chaleureux, inspirant
Langue: Français
Public: Communauté chrétienne haïtienne
Important: Sois fidèle au contenu exact de la leçon, pas générique"""
    else:
        prompt = f"""Génère un Sabbat School Nugget pour {jour} {today}, Leçon {lecon_num} du trimestre adventiste sur "Grandir dans sa relation avec Dieu".

Format:
- Ouverture inspirante
- Verset biblique clé
- Leçon principale (3-4 phrases)
- Application pratique
- Prière courte

Ton: sage, chaleureux, inspirant. Langue: Français."""

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text, titre_lecon

def generate_audio(text, filename):
    """Génère l'audio avec ElevenLabs"""
    api_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVEN_KEY", "")
    if not api_key:
        print("[!] ELEVENLABS_API_KEY manquant")
        return False
    try:
        import requests as req
        voice_id = "onwK4e9ZLuTAKqWW03F9"  # Daniel - sage
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.7, "similarity_boost": 0.8}
        }
        r = req.post(url, json=data, headers=headers)
        if r.status_code == 200:
            Path(filename).write_bytes(r.content)
            return True
        print(f"[!] ElevenLabs erreur: {r.status_code}")
        return False
    except Exception as e:
        print(f"[!] Audio erreur: {e}")
        return False

def run():
    print("""
╔══════════════════════════════════════════════╗
║   SABBAT SCHOOL NUGGET — LEÇON DU JOUR      ║
╚══════════════════════════════════════════════╝
    """)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_str = date.today().isoformat()
    
    print("[1/3] Extraction de la leçon du jour...")
    text, theme = generate_sabbat_text()
    print(f"[OK] Thème: {theme}")
    
    print("[2/3] Sauvegarde du texte...")
    txt_file = SABBAT_DIR / f"{date_str}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(f"SABBAT SCHOOL NUGGET\n")
        f.write(f"Date: {date_str}\n")
        f.write(f"Thème: {theme}\n")
        f.write("="*50 + "\n\n")
        f.write(text)
    print(f"[OK] Texte: {txt_file.name}")
    
    print("[3/3] Génération audio...")
    mp3_file = SABBAT_DIR / f"{date_str}.mp3"
    success = generate_audio(text, str(mp3_file))
    if success:
        print(f"[OK] Audio: {mp3_file.name}")
    
    print(f"\n✅ Sabbat Nugget généré!\n   📅 {date_str}\n   📖 {theme}\n")

if __name__ == "__main__":
    run()
