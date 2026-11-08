#!/usr/bin/env python3
"""lister_modeles.py - Affiche les modeles visibles par VOTRE cle Gemini."""
import os
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

tous, tts = [], []
try:
    for m in client.models.list():
        nom = getattr(m, "name", str(m)).replace("models/", "")
        tous.append(nom)
        if "tts" in nom.lower() or "speech" in nom.lower() or "audio" in nom.lower():
            tts.append(nom)
except Exception as e:
    raise SystemExit(f"Impossible de lister : {e}")

print(f"\n{len(tous)} modeles visibles par votre cle.\n")
print("=== MODELES VOIX / TTS ===")
if tts:
    for n in sorted(tts):
        print("   ", n)
else:
    print("    AUCUN modele TTS visible par cette cle.")

print("\n=== Les 3.x presents (tous types) ===")
trois = [n for n in tous if n.startswith("gemini-3")]
for n in sorted(trois)[:25]:
    print("   ", n)
if not trois:
    print("    aucun modele gemini-3.x")

Path("modeles_disponibles.txt").write_text("\n".join(sorted(tous)), encoding="utf-8")
print(f"\nListe complete ecrite dans modeles_disponibles.txt")
