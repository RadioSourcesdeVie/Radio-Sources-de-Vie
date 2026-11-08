#!/usr/bin/env python3
"""diag2.py - Cherche les modeles TTS sur v1, v1beta et v1alpha."""
import os, base64, json, urllib.request
from pathlib import Path
from google import genai

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

charger_env()
CLE = os.environ.get("GEMINI_KEY", "")
if not CLE:
    raise SystemExit("GEMINI_KEY introuvable dans .env")

print("\n=== 1. Liste des modeles par version d'API (REST direct) ===")
trouve = {}
for ver in ("v1", "v1beta", "v1alpha"):
    url = f"https://generativelanguage.googleapis.com/{ver}/models?key={CLE}&pageSize=200"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read())
        noms = [m["name"].replace("models/", "") for m in data.get("models", [])]
        tts = sorted(n for n in noms if "tts" in n.lower())
        trouve[ver] = tts
        print(f"\n  {ver} : {len(noms)} modeles, {len(tts)} TTS")
        for n in tts:
            print(f"      {n}")
    except Exception as e:
        print(f"\n  {ver} : erreur -> {str(e)[:90]}")

print("\n=== 2. Generation TTS via REST v1beta (ancienne forme) ===")
cibles = sorted({n for lst in trouve.values() for n in lst}) or \
         ["gemini-2.5-flash-preview-tts", "gemini-3.8-flash-tts"]
OUT = Path("diag_tts"); OUT.mkdir(exist_ok=True)

for modele in cibles[:4]:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{modele}:generateContent?key={CLE}")
    corps = {
        "contents": [{"parts": [{"text": "Que la paix du Seigneur soit avec vous."}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}
            },
        },
    }
    req = urllib.request.Request(
        url, data=json.dumps(corps).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read())
        b64 = d["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        brut = base64.b64decode(b64)
        f = OUT / f"REST_{modele}.pcm"
        f.write_bytes(brut)
        print(f"  OK   {modele} -> {f.name}  {len(brut)//1024} KB")
    except Exception as e:
        msg = str(e)
        if hasattr(e, "read"):
            try:
                msg = e.read().decode()[:200]
            except Exception:
                pass
        print(f"  non  {modele} : {msg[:150]}")

print("\n=== 3. SDK force sur v1beta ===")
for ver in ("v1beta", "v1alpha"):
    try:
        c = genai.Client(api_key=CLE, http_options={"api_version": ver})
        noms = [getattr(m, "name", "").replace("models/", "") for m in c.models.list()]
        tts = sorted(n for n in noms if "tts" in n.lower())
        print(f"  {ver} : {len(noms)} modeles, TTS = {tts if tts else 'aucun'}")
    except Exception as e:
        print(f"  {ver} : erreur -> {str(e)[:90]}")

print("\nTermine.")
