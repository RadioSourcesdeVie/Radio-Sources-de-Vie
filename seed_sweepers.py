#!/usr/bin/env python3
"""
seed_sweepers.py — Lance UNE SEULE FOIS pour générer l'audio des 3 premiers
sweepers FR + 3 EN déjà écrits et approuvés avec Souvenan, et les enregistrer
dans content/sweepers/index.json (même format que generate_sweepers.py).

Après ce lancement unique, les prochains lots seront écrits automatiquement
par Claude via generate_sweepers.py --api-key ..., programmé chaque semaine.
"""
import asyncio, json, re
from datetime import datetime
from pathlib import Path
import shutil
import edge_tts

TODAY = datetime.now().strftime("%Y-%m-%d")

VOICE_FR = "fr-FR-HenriNeural"
VOICE_EN = "en-US-GuyNeural"

OUT_FR_DIR = Path("Nouvelles/Radio SDV SweepersFR")
OUT_EN_DIR = Path("Nouvelles/Radio SDV SweepersEN")
BATCH_DIR  = Path("audio/sweepers")
INDEX_PATH = Path("content/sweepers/index.json")

SWEEPERS_FR = [
    {"slug": "philippiens4-6", "reference": "Philippiens 4:6",
     "text": "Le saviez-vous ? Il existe un verset depuis 2000 ans... juste pour "
              "vous dire d'arrêter de stresser. Philippiens 4:6. "
              "Vous écoutez Radio Sources de Vie, le chemin du salut."},
    {"slug": "ecclesiaste3-1", "reference": "Ecclésiaste 3:1",
     "text": "Le saviez-vous que Dieu ne fait jamais la queue à l'épicerie, mais Il "
              "vous demande d'être patient ? Ecclésiaste 3:1. "
              "Vous écoutez Radio Sources de Vie, le chemin du salut."},
    {"slug": "matthieu18-22", "reference": "Matthieu 18:22",
     "text": "Le saviez-vous que pardonner 70 fois 7 fois, c'est plus que les fois "
              "où votre belle-mère vous énerve ? Matthieu 18:22. "
              "Vous écoutez Radio Sources de Vie, le chemin du salut."},
]

SWEEPERS_EN = [
    {"slug": "philippians4-6", "reference": "Philippians 4:6",
     "text": "Did you know there's a verse that's existed for two thousand years... "
              "just to tell you to stop stressing? Philippians 4:6. "
              "You're listening to Radio Sources de Vie — the way to salvation."},
    {"slug": "ecclesiastes3-1", "reference": "Ecclesiastes 3:1",
     "text": "Did you know God never waits in line at the grocery store, but He "
              "asks you to be patient? Ecclesiastes 3:1. "
              "You're listening to Radio Sources de Vie — the way to salvation."},
    {"slug": "matthew18-22", "reference": "Matthew 18:22",
     "text": "Did you know forgiving seventy times seven is still more than the "
              "times your mother-in-law annoyed you this year? Matthew 18:22. "
              "You're listening to Radio Sources de Vie — the way to salvation."},
]


STATION_NAME_FR = "Radio Sources de Vie"

def clean_reference_fr(text: str) -> str:
    """"Philippiens 4:6" -> "Philippiens 4 verset 6" (sinon Edge TTS lit ça comme une heure)."""
    text = re.sub(r'(\d+):(\d+)-(\d+)', r'\1 verset \2 à \3', text)
    text = re.sub(r'(\d+):(\d+)', r'\1 verset \2', text)
    return text

def clean_reference_en(text: str) -> str:
    """"Philippians 4:6" -> "Philippians 4 verse 6" (otherwise Edge TTS reads it as a time)."""
    text = re.sub(r'(\d+):(\d+)-(\d+)', r'\1 verse \2 to \3', text)
    text = re.sub(r'(\d+):(\d+)', r'\1 verse \2', text)
    return text

async def _synth_bytes(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    audio = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
    return bytes(audio)

def synth_with_station_name(text: str, main_voice: str) -> bytes:
    """Synthétise le texte avec main_voice, mais toujours avec l'accent
    français correct pour "Radio Sources de Vie", peu importe la langue
    de la voix principale (utile pour les sweepers en anglais)."""
    if STATION_NAME_FR not in text or main_voice == VOICE_FR:
        return asyncio.run(_synth_bytes(text, main_voice))
    parts = text.split(STATION_NAME_FR)
    audio = bytearray()
    for i, part in enumerate(parts):
        if part.strip():
            audio.extend(asyncio.run(_synth_bytes(part, main_voice)))
        if i < len(parts) - 1:
            audio.extend(asyncio.run(_synth_bytes(STATION_NAME_FR, VOICE_FR)))
    return bytes(audio)


def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return []


def save_index(index):
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def synth_language(sweepers, lang, voice, out_dir, index):
    out_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    for sw in sweepers:
        out_file = out_dir / f"sweeper_{lang}_{TODAY}_{sw['slug']}.mp3"
        if out_file.exists():
            print(f"⏭️  {lang} {sw['slug']}: déjà généré")
        else:
            print(f"🎤 {lang} {sw['slug']}...")
            clean_text = clean_reference_fr(sw["text"]) if lang == "fr" else clean_reference_en(sw["text"])
            audio = synth_with_station_name(clean_text, voice)
            out_file.write_bytes(audio)
            print(f"✅ → {out_file} ({len(audio)//1024} KB)")
            index.append({
                "language": lang,
                "slug": sw["slug"],
                "reference": sw["reference"],
                "text": sw["text"],
                "audio_file": str(out_file).replace("\\", "/"),
                "date_added": TODAY,
            })
        clips.append(out_file)
    return clips


def copy_backup_clips(clips, out_dir):
    """Copie chaque clip individuellement (pas de fichier combiné) dans le
    dossier de sauvegarde audio/sweepers/FR ou EN — mêmes fichiers que
    Nouvelles/Radio SDV Sweepers{FR,EN}, juste une deuxième copie."""
    out_dir.mkdir(parents=True, exist_ok=True)
    for c in clips:
        dest = out_dir / Path(c).name
        shutil.copy2(c, dest)
    print(f"✅ Copie de sauvegarde ({len(clips)} fichiers) → {out_dir}")


def main():
    print(f"\n📻 Semis du premier lot de sweepers — {TODAY}\n")
    index = load_index()

    fr_clips = synth_language(SWEEPERS_FR, "fr", VOICE_FR, OUT_FR_DIR, index)
    en_clips = synth_language(SWEEPERS_EN, "en", VOICE_EN, OUT_EN_DIR, index)

    save_index(index)

    copy_backup_clips(fr_clips, BATCH_DIR / "FR")
    copy_backup_clips(en_clips, BATCH_DIR / "EN")

    print(f"\n✅ Terminé. Historique initialisé dans {INDEX_PATH}")
    print("   Les prochains lots seront écrits automatiquement chaque semaine par generate_sweepers.py")


if __name__ == "__main__":
    main()
