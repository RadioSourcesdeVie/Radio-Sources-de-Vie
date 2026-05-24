# -*- coding: utf-8 -*-
"""
Radio Sources de Vie - Utilitaires communs
Voix: Gemini Aoede | Langue: Français uniquement
"""
import os
import sys
import wave
import json
import base64
import datetime
import subprocess
from pathlib import Path

GEMINI_API_KEY = "AIzaSyCwohhMyTUi9tM-Ry34DCqYdbrwTi-ctI8"
VOICE_NAME = "Aoede"
TTS_MODEL_PRIMARY = "gemini-2.5-flash-preview-tts"
TTS_MODEL_FALLBACK = "gemini-2.5-pro-preview-tts"
TEXT_MODEL = "gemini-2.5-flash"
STATION_NAME = "Radio Sources de Vie"
SAMPLE_RATE = 24000  # 24 kHz PCM from Gemini TTS

# Les scripts vivent dans <projet>/scripts/, mais les sorties audio (priere/,
# nouvelles/, sermon/, temoignage/) et le dossier state/ restent à la racine
# du projet pour RadioDJ et la planification.
# BASE_DIR = racine du projet (un niveau au-dessus de scripts/).
SCRIPTS_DIR = Path(__file__).parent
BASE_DIR = SCRIPTS_DIR.parent
STATE_DIR = BASE_DIR / "state"
STATE_DIR.mkdir(exist_ok=True)


def get_client():
    """Retourne un client Gemini configuré."""
    from google import genai
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_text(prompt: str) -> str:
    """Génère du texte avec Gemini. Retry sur erreurs serveur transitoires (5xx)."""
    import time
    client = get_client()

    last_err = None
    for attempt in range(1, 6):  # 5 tentatives, backoff exponentiel
        try:
            response = client.models.generate_content(
                model=TEXT_MODEL,
                contents=prompt
            )
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            return response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            last_err = e
            err_str = str(e)
            transient = any(c in err_str for c in ('500', '502', '503', '504',
                                                   'UNAVAILABLE', 'INTERNAL',
                                                   'DEADLINE', 'RESOURCE_EXHAUSTED'))
            if not transient or attempt == 5:
                raise
            delai = min(60, 5 * (2 ** (attempt - 1)))  # 5s, 10s, 20s, 40s, plafonné à 60s
            print(f"  Texte: erreur transitoire (tentative {attempt}/5), nouvel essai dans {delai}s...")
            time.sleep(delai)
    raise last_err


def split_text(text: str, max_chars: int = 4500) -> list:
    """Découpe un long texte en morceaux pour la synthèse vocale."""
    if len(text) <= max_chars:
        return [text]

    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= max_chars:
            chunks.append(remaining)
            break
        split_at = max(
            remaining.rfind('. ', 0, max_chars),
            remaining.rfind('! ', 0, max_chars),
            remaining.rfind('? ', 0, max_chars),
            remaining.rfind('\n\n', 0, max_chars),
        )
        if split_at <= 50:
            split_at = max_chars
        else:
            split_at += 2

        chunk = remaining[:split_at].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].strip()

    return [c for c in chunks if c.strip()]


def _tts_chunk(client, text: str) -> bytes:
    """Convertit un morceau de texte en audio PCM via Gemini TTS (avec retries)."""
    import time
    from google.genai import types

    tts_config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=VOICE_NAME
                )
            )
        )
    )

    models_to_try = [TTS_MODEL_PRIMARY, TTS_MODEL_FALLBACK]

    for model in models_to_try:
        for attempt in range(1, 4):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=text,
                    config=tts_config
                )
                audio_data = response.candidates[0].content.parts[0].inline_data.data
                if isinstance(audio_data, str):
                    audio_data = base64.b64decode(audio_data)
                return audio_data
            except Exception as e:
                err_str = str(e)
                if '500' in err_str or 'INTERNAL' in err_str or '503' in err_str or 'UNAVAILABLE' in err_str:
                    print(f"  TTS erreur serveur (tentative {attempt}/3, modèle {model}): réessai...")
                    time.sleep(3 * attempt)
                else:
                    print(f"  TTS erreur ({model}): {err_str[:80]}")
                    break

    raise RuntimeError("Synthèse vocale échouée après toutes les tentatives.")


def text_to_speech(text: str) -> bytes:
    """Convertit le texte complet en audio via Gemini TTS (voix Aoede)."""
    client = get_client()
    chunks = split_text(text, max_chars=4500)
    all_audio = b""

    for i, chunk in enumerate(chunks, 1):
        if not chunk.strip():
            continue
        print(f"  Synthèse vocale {i}/{len(chunks)}...")
        all_audio += _tts_chunk(client, chunk)

    return all_audio


def save_audio(audio_data: bytes, output_path: str) -> str:
    """Sauvegarde les données audio en WAV."""
    wav_path = output_path if output_path.endswith('.wav') else output_path.replace('.mp3', '.wav')

    dir_path = os.path.dirname(wav_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    is_wav_format = len(audio_data) > 4 and audio_data[:4] == b'RIFF'

    if is_wav_format:
        with open(wav_path, 'wb') as f:
            f.write(audio_data)
    else:
        with wave.open(wav_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_data)

    print(f"  WAV sauvegardé: {wav_path}")
    return wav_path


def save_script(text: str, output_path: str):
    """Sauvegarde le script texte."""
    dir_path = os.path.dirname(output_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"  Script TXT sauvegardé: {output_path}")


def get_timestamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def get_topic_index(state_file: str, num_topics: int) -> int:
    """Retourne l'index du prochain sujet en rotation."""
    state_path = STATE_DIR / state_file
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        last_index = state.get('last_index', -1)
    except Exception:
        last_index = -1

    next_index = (last_index + 1) % num_topics

    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump({'last_index': next_index, 'updated': get_timestamp()}, f)

    return next_index


def intro_text() -> str:
    return "Vous écoutez Radio Sources de Vie."


def outro_text() -> str:
    return "Merci d'être avec nous sur Radio Sources de Vie, que Dieu vous bénisse!"


def build_full_script(content: str, title: str = "") -> tuple:
    """Construit le script complet avec intro/outro et retourne (script_complet, texte_tts)."""
    header = f"[JINGLE INTRO]\n\n{intro_text()}"
    footer = f"{outro_text()}\n\n[JINGLE OUTRO]"

    if title:
        full_script = f"{header}\n\n--- {title} ---\n\n{content}\n\n{footer}"
    else:
        full_script = f"{header}\n\n{content}\n\n{footer}"

    tts_text = f"{intro_text()}\n\n{content}\n\n{outro_text()}"

    return full_script, tts_text
