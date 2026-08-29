# -*- coding: utf-8 -*-
"""
Kit Radio IA - Génération de texte (Claude / Anthropic)
Toutes les valeurs viennent de config.py.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

BASE_DIR = Path(__file__).parent.parent


def verifier_config():
    problemes = []
    if not config.ANTHROPIC_API_KEY or "COLLEZ_VOTRE" in config.ANTHROPIC_API_KEY:
        problemes.append("ANTHROPIC_API_KEY n'est pas configurée dans config.py")
    if config.TTS_PROVIDER == "elevenlabs" and "COLLEZ_VOTRE" in config.ELEVENLABS_API_KEY:
        problemes.append("TTS_PROVIDER=elevenlabs mais ELEVENLABS_API_KEY n'est pas configurée")
    if config.TTS_PROVIDER == "gemini" and "COLLEZ_VOTRE" in config.GEMINI_API_KEY:
        problemes.append("TTS_PROVIDER=gemini mais GEMINI_API_KEY n'est pas configurée")
    if problemes:
        print("ATTENTION - config.py incomplet:")
        for p in problemes:
            print(f"  - {p}")
        sys.exit(1)


def _client():
    import anthropic
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def generate_text(prompt: str, system: str = None, max_tokens: int = 1200) -> str:
    """Génère du texte libre avec Claude."""
    client = _client()
    kwargs = {"model": config.CLAUDE_MODEL, "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]}
    if system:
        kwargs["system"] = system
    msg = client.messages.create(**kwargs)
    return msg.content[0].text.strip()


def generate_json(prompt: str, system: str = None, max_tokens: int = 1200) -> dict:
    """Génère du texte avec Claude et parse le premier objet/tableau JSON trouvé."""
    raw = generate_text(prompt, system=system, max_tokens=max_tokens)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    start = min((i for i in (raw.find("{"), raw.find("[")) if i != -1), default=0)
    data, _ = json.JSONDecoder().raw_decode(raw[start:])
    return data


def get_recent(content_dir: str, prefix: str = "", field: str = "reference", days: int = 7) -> list:
    """Lit un champ (ex: référence biblique, titre) des N derniers jours pour éviter les répétitions."""
    from datetime import datetime, timedelta
    valeurs = []
    dossier = BASE_DIR / content_dir
    for i in range(1, days + 1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        f = dossier / f"{prefix}{date}.json"
        if f.exists():
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                if d.get(field):
                    valeurs.append(d[field])
            except Exception:
                pass
    return valeurs


def clean_markdown(text: str) -> str:
    """Retire le formatage markdown que l'IA ajoute parfois (**, #, _)."""
    import re
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    return text.replace('*', '').replace('#', '').strip()


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path):
    if not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))
