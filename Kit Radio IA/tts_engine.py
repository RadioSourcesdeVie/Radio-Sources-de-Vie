# -*- coding: utf-8 -*-
"""
Kit Radio IA - Moteur de synthèse vocale (voix)
Fournisseur choisi dans config.TTS_PROVIDER : "edge" (gratuit), "elevenlabs"
ou "gemini". Toutes les fonctions du kit appellent uniquement synth_to_file()
ci-dessous — le reste du kit ignore quel fournisseur est actif.
"""
import sys
import re
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config


def clean_for_tts(text: str) -> str:
    """Retire le markdown et corrige les références bibliques (ex: "4:6" lu
    comme une heure) avant de les envoyer à la synthèse vocale."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'_{1,2}(.*?)_{1,2}', r'\1', text)
    text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = text.replace('*', '').replace('#', '').replace('_', ' ')
    text = re.sub(r'(\d+):(\d+)-(\d+)', r'\1 verset \2 à \3', text)
    text = re.sub(r'(\d+):(\d+)', r'\1 verset \2', text)
    return text.strip()


# ---------------------------------------------------------------
# Fournisseur : Edge TTS (Microsoft, gratuit, aucune clé requise)
# ---------------------------------------------------------------
async def _edge_synth_bytes(text: str, voice: str) -> bytes:
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)


def _edge_synth(text: str, role: str) -> bytes:
    voice = config.EDGE_VOICES[role]
    return asyncio.run(_edge_synth_bytes(text, voice))


# ---------------------------------------------------------------
# Fournisseur : ElevenLabs (payant, qualité premium)
# ---------------------------------------------------------------
def _elevenlabs_synth(text: str, role: str) -> bytes:
    import requests
    voice_id = config.ELEVENLABS_VOICES[role]
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": config.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": config.ELEVENLABS_MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.content


# ---------------------------------------------------------------
# Fournisseur : Google Gemini TTS (payant au-delà du quota gratuit)
# ---------------------------------------------------------------
def _gemini_synth(text: str, role: str) -> bytes:
    import base64
    from google import genai
    from google.genai import types

    voice_name = config.GEMINI_VOICES[role]
    client = genai.Client(api_key=config.GEMINI_API_KEY)
    tts_config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
            )
        )
    )
    response = client.models.generate_content(
        model=config.GEMINI_TTS_MODEL, contents=text, config=tts_config
    )
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    if isinstance(audio_data, str):
        audio_data = base64.b64decode(audio_data)
    return _pcm_to_wav_bytes(audio_data)


def _pcm_to_wav_bytes(pcm: bytes, sample_rate: int = 24000) -> bytes:
    import io
    import wave
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return buf.getvalue()


# ---------------------------------------------------------------
# Point d'entrée unique
# ---------------------------------------------------------------
_PROVIDERS = {
    "edge": _edge_synth,
    "elevenlabs": _elevenlabs_synth,
    "gemini": _gemini_synth,
}

# Edge TTS et ElevenLabs renvoient du MP3 ; Gemini renvoie du PCM que nous
# encapsulons en WAV (RadioDJ lit très bien le WAV). Utilisez cette fonction
def output_extension() -> str:
    """Extension de fichier correcte selon le fournisseur actif."""
    return "wav" if config.TTS_PROVIDER == "gemini" else "mp3"


def synth(text: str, role: str) -> bytes:
    """Synthétise `text` avec la voix associée au rôle (ex: 'sermon',
    'presentateur_a'), selon le fournisseur choisi dans config.TTS_PROVIDER."""
    fournisseur = _PROVIDERS.get(config.TTS_PROVIDER)
    if fournisseur is None:
        raise ValueError(f"TTS_PROVIDER inconnu dans config.py: {config.TTS_PROVIDER!r}")
    return fournisseur(clean_for_tts(text), role)


def synth_to_file(text: str, role: str, output_path) -> int:
    """Synthétise et sauvegarde dans output_path (l'extension doit correspondre
    à output_extension() — voir helper `chemin_audio()` dans les scripts).
    Retourne la taille en Ko."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio = synth(text, role)
    output_path.write_bytes(audio)
    return len(audio) // 1024


def chemin_audio(dossier, nom_base: str) -> Path:
    """Construit un chemin de fichier audio avec la bonne extension pour le
    fournisseur TTS actif (ex: chemin_audio(BASE_DIR / "audio", "sermon_2026-08-29"))."""
    return Path(dossier) / f"{nom_base}.{output_extension()}"


def synth_duo_to_file(segments: list, output_path) -> int:
    """segments: liste de (texte, role). Concatène les audios dans l'ordre
    (utilisé pour le journal du soir en duo de présentateurs)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audio = bytearray()
    for text, role in segments:
        if not text or not text.strip():
            continue
        audio.extend(synth(text, role))
    output_path.write_bytes(bytes(audio))
    return len(audio) // 1024
