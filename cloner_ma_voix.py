#!/usr/bin/env python3
"""
cloner_ma_voix.py - Cree une voix repliquee a partir de 2 enregistrements.

Prerequis dans le dossier du site :
    ma_voix/reference.wav      10 a 30 s de VOTRE voix (predication ou lecture)
    ma_voix/consentement.wav   la phrase de consentement, lue par VOUS

Usage:  python cloner_ma_voix.py
Ecrit : ma_voix/voice_id.txt   (identifiant a utiliser ensuite)
"""
import os, base64, wave
from pathlib import Path
from google import genai

MODEL   = "gemini-3.8-flash-tts"
DOSSIER = Path("ma_voix")
REF     = DOSSIER / "reference.wav"
CONSENT = DOSSIER / "consentement.wav"
SORTIE  = DOSSIER / "voice_id.txt"
NOM     = "Pasteur Souvenan"

PHRASE = ("Je suis le proprietaire de cette voix et j'autorise Google "
          "a utiliser cette voix pour creer un modele de voix synthetique.")

def verifier(p, mini, maxi):
    """Controle format et duree avant d'envoyer quoi que ce soit."""
    if not p.exists():
        raise SystemExit(f"Fichier manquant : {p}")
    with wave.open(str(p), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
    duree = n / float(sr)
    print(f"  {p.name:<20} {duree:5.1f} s  {sr} Hz  {ch} canal(aux)  {sw*8} bits")
    souci = []
    if ch != 1:        souci.append("doit etre MONO")
    if sr != 24000:    souci.append(f"doit etre 24000 Hz (actuel {sr})")
    if sw != 2:        souci.append("doit etre 16 bits")
    if not (mini <= duree <= maxi):
        souci.append(f"duree hors limites ({mini}-{maxi} s)")
    if souci:
        raise SystemExit("  PROBLEME : " + " ; ".join(souci))
    return True

def b64(p):
    return base64.b64encode(p.read_bytes()).decode("utf-8")

def charger_env():
    """Lit .env directement : fonctionne avec ou sans 'export'."""
    p = Path(".env")
    if not p.exists():
        return
    for ligne in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        if ligne.startswith("export "):
            ligne = ligne[7:].strip()
        k, _, v = ligne.partition("=")
        v = v.strip().strip('"').strip("'")
        if k.strip() and v:
            os.environ.setdefault(k.strip(), v)

def main():
    charger_env()
    cle = os.environ.get("GEMINI_KEY", "")
    if not cle:
        raise SystemExit("GEMINI_KEY introuvable dans .env.\nAjoutez une ligne :  GEMINI_KEY=votre_cle")

    print("\nVerification des enregistrements :")
    verifier(REF, 10, 30)
    verifier(CONSENT, 3, 30)

    print(f"\nPhrase de consentement attendue :\n  \"{PHRASE}\"\n")

    # Les modeles TTS ne sont exposes que sur v1beta
    client = genai.Client(api_key=cle, http_options={"api_version": "v1beta"})
    print("Envoi a Google (verification du locuteur en cours)...")
    voix = client.voices.create(
        store=True,
        voice={
            "model": MODEL,
            "type": "replicated",
            "display_name": NOM,
            "replicated": {
                "source_audio":  {"mime_type": "audio/wav", "data": b64(REF)},
                "consent_audio": {"mime_type": "audio/wav", "data": b64(CONSENT)},
            },
        },
    )
    SORTIE.write_text(voix.id, encoding="utf-8")
    print(f"\nOK - voix creee : {voix.id}")
    print(f"Identifiant enregistre dans {SORTIE}")
    print("Valable 1 an. Gardez les 2 WAV pour pouvoir la recreer.")

    # Echantillon de controle
    essai = ("Bienvenue sur Radio Sources de Vie. Que la paix du Seigneur "
             "soit avec vous en ce jour.")
    r = client.interactions.create(
        model=MODEL,
        input=[{"type": "user_input", "content": [{"type": "text", "text": essai}]}],
        response_format={"type": "audio"},
        generation_config={"speech_config": [{"voice": voix.id}]},
    )
    out = DOSSIER / "essai_ma_voix.wav"
    out.write_bytes(base64.b64decode(r.output_audio.data))
    print(f"\nEchantillon a ecouter : {out}")

if __name__ == "__main__":
    main()
