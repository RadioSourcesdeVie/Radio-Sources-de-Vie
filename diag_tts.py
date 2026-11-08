#!/usr/bin/env python3
"""diag_tts.py - Trouve quel modele TTS fonctionne avec VOTRE cle."""
import os, base64
from pathlib import Path
from google import genai

def charger_env():
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

charger_env()
cle = os.environ.get("GEMINI_KEY", "")
if not cle:
    raise SystemExit("GEMINI_KEY introuvable dans .env")

client = genai.Client(api_key=cle)
TEXTE = "Que la paix du Seigneur soit avec vous."
OUT = Path("diag_tts"); OUT.mkdir(exist_ok=True)

NOUVEAUX = [
    "gemini-3.8-flash-tts",
    "gemini-3.8-flash-lite-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-3.1-flash-tts",
]
ANCIENS = [
    "gemini-2.5-flash-preview-tts",
    "gemini-2.5-pro-preview-tts",
]

def court(e):
    s = str(e).replace("\n", " ")
    return s[:110]

print("\n=== FORME A : interactions.create (API 3.8) ===")
for m in NOUVEAUX:
    try:
        r = client.interactions.create(
            model=m,
            input=[{"type": "user_input",
                    "content": [{"type": "text", "text": TEXTE}]}],
            response_format={"type": "audio"},
            generation_config={"speech_config": [{"voice": "Kore"}]},
        )
        f = OUT / f"A_{m}.wav"
        f.write_bytes(base64.b64decode(r.output_audio.data))
        print(f"  OK   {m}  -> {f.name}  {f.stat().st_size//1024} KB")
    except Exception as e:
        print(f"  non  {m}  : {court(e)}")

print("\n=== FORME B : models.generate_content (API 2.5) ===")
try:
    from google.genai import types
    for m in ANCIENS + NOUVEAUX:
        try:
            r = client.models.generate_content(
                model=m,
                contents=TEXTE,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Kore")))),
            )
            d = r.candidates[0].content.parts[0].inline_data.data
            if isinstance(d, str):
                d = base64.b64decode(d)
            f = OUT / f"B_{m}.pcm"
            f.write_bytes(d)
            print(f"  OK   {m}  -> {f.name}  {len(d)//1024} KB")
        except Exception as e:
            print(f"  non  {m}  : {court(e)}")
except Exception as e:
    print(f"  types indisponibles : {court(e)}")

print("\nFichiers produits dans le dossier diag_tts/ (s'il y en a).")
