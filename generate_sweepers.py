#!/usr/bin/env python3
"""
generate_sweepers.py — Sweepers "Le saviez-vous ?" avec versets bibliques
Radio Sources de Vie Chrétienne
Texte: Claude (généré automatiquement, thème + verset différents à chaque lot).
Audio: Edge TTS (Microsoft, gratuit, sans clé API).

Règle de cadence (donnée par Souvenan) :
  - Lot de 3 sweepers  → régénérer CHAQUE SEMAINE (BATCH_SIZE = 3 ci-dessous)
  - Lot de 10+ sweepers → régénérer CHAQUE MOIS
Actuellement configuré pour un lot de 3 (cadence hebdomadaire). Pour passer à
un lot mensuel de 10+, changer BATCH_SIZE et reprogrammer la tâche planifiée.

Génère à chaque exécution :
  1) De nouveaux textes (FR + EN), verset différent des lots précédents
     (historique lu dans content/sweepers/index.json)
  2) Un fichier audio individuel par sweeper dans Nouvelles/Radio SDV SweepersFR/
     et Nouvelles/Radio SDV SweepersEN/
     (RadioDJ les fait tourner au hasard entre les segments)
  3) Un fichier "batch" combiné par langue dans audio/sweepers/ (aperçu)
  4) Mise à jour de content/sweepers/index.json (historique anti-répétition)
"""
import anthropic, asyncio, json, argparse, re
from datetime import datetime
from pathlib import Path
import shutil
import edge_tts

TODAY = datetime.now().strftime("%Y-%m-%d")
BATCH_SIZE = 3  # 3 => cadence hebdomadaire ; 10+ => cadence mensuelle (voir en-tête)

VOICE_FR = "fr-FR-HenriNeural"   # Henri — voix chaleureuse déjà utilisée pour le sermon
VOICE_EN = "en-US-GuyNeural"     # Guy — voix anglaise décontractée, ton léger

OUT_FR_DIR = Path("Nouvelles/Radio SDV SweepersFR")
OUT_EN_DIR = Path("Nouvelles/Radio SDV SweepersEN")
BATCH_DIR  = Path("audio/sweepers")
INDEX_PATH = Path("content/sweepers/index.json")

SYSTEM_FR = ("Tu écris des sweepers radio pour Radio Sources de Vie, une radio chrétienne "
             "francophone pour la diaspora haïtienne au Canada. Ton style: léger, drôle, "
             "format 'Le saviez-vous...' suivi d'une petite blague ou observation du "
             "quotidien, puis une chute vers un vrai verset biblique (Louis Segond) en lien "
             "avec le sujet. Jamais moqueur envers la foi elle-même — la blague porte sur la "
             "vie de tous les jours, pas sur la Bible.")

SYSTEM_EN = ("You write radio sweepers for Radio Sources de Vie, a French-language Christian "
             "station for the Haitian diaspora in Canada, but these specific sweepers air in "
             "English. Style: light, funny, 'Did you know...' format followed by a small joke "
             "or everyday observation, landing on a real Bible verse (any standard English "
             "translation) related to the topic. Never mock the faith itself — the joke is "
             "about everyday life, not the Bible.")

PROMPT_TEMPLATE_FR = """Écris {n} sweepers radio différents pour Radio Sources de Vie.

Chaque sweeper doit :
- Faire 8 à 12 secondes à l'oral (environ 25 à 32 mots, référence biblique incluse)
- Suivre le format : "Le saviez-vous... [observation drôle du quotidien] ? [Référence]. Vous écoutez Radio Sources de Vie, le chemin du salut."
- Utiliser un verset biblique DIFFÉRENT des versets suivants déjà utilisés récemment :
{avoid}
- Être vraiment drôle/léger, pas juste une info biblique sèche

Réponds UNIQUEMENT en JSON, une liste de {n} objets :
[{{"slug":"identifiant-court-sans-accents","reference":"Livre Ch:V","text":"texte complet du sweeper"}}, ...]"""

PROMPT_TEMPLATE_EN = """Write {n} different radio sweepers for Radio Sources de Vie (airing in English).

Each sweeper must:
- Run 8 to 12 seconds spoken (about 25 to 32 words, including the Bible reference)
- Follow the format: "Did you know... [funny everyday observation]? [Reference]. You're listening to Radio Sources de Vie — the way to salvation."
- Use a Bible verse DIFFERENT from these already used recently:
{avoid}
- Be genuinely funny/light, not just a dry Bible fact

Respond ONLY in JSON, a list of {n} objects:
[{{"slug":"short-id-no-accents","reference":"Book Ch:V","text":"full sweeper text"}}, ...]"""


def load_index():
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return []


def save_index(index):
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def recent_references(index, lang, limit=40):
    refs = [e["reference"] for e in index if e.get("language") == lang]
    return refs[-limit:] if refs else []


def gen_sweepers(client, lang, n, avoid_refs):
    system = SYSTEM_FR if lang == "fr" else SYSTEM_EN
    template = PROMPT_TEMPLATE_FR if lang == "fr" else PROMPT_TEMPLATE_EN
    avoid_text = "\n".join(f"  - {r}" for r in avoid_refs) if avoid_refs else "  (aucun / none)"
    prompt = template.format(n=n, avoid=avoid_text)
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1200,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    start = raw.find("[")
    data, _ = json.JSONDecoder().raw_decode(raw[start:])
    return data


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


def slugify(s):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "sweeper"


def clear_radiodj_folder(out_dir):
    """Vide le dossier RadioDJ (Nouvelles/Radio SDV Sweepers{FR,EN}) avant d'y
    déposer le nouveau lot — RadioDJ ne doit jamais avoir un mélange d'anciens
    et de nouveaux sweepers, sinon rotation confuse. L'archive (audio/sweepers)
    n'est JAMAIS vidée, elle garde tout l'historique."""
    if not out_dir.exists():
        return
    removed = 0
    for f in out_dir.glob("*.mp3"):
        f.unlink()
        removed += 1
    if removed:
        print(f"🗑️  {removed} ancien(s) fichier(s) retiré(s) de {out_dir}")


def synth_language(sweepers, lang, voice, out_dir, index):
    out_dir.mkdir(parents=True, exist_ok=True)
    clear_radiodj_folder(out_dir)
    clips = []
    for sw in sweepers:
        slug = slugify(sw.get("slug") or sw["reference"])
        out_file = out_dir / f"sweeper_{lang}_{TODAY}_{slug}.mp3"
        print(f"🎤 {lang} — {sw['reference']}...")
        clean_text = clean_reference_fr(sw["text"]) if lang == "fr" else clean_reference_en(sw["text"])
        audio = synth_with_station_name(clean_text, voice)
        out_file.write_bytes(audio)
        print(f"✅ → {out_file} ({len(audio)//1024} KB)")
        index.append({
            "language": lang,
            "slug": slug,
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-key", required=True, help="Clé Anthropic")
    args = parser.parse_args()
    client = anthropic.Anthropic(api_key=args.api_key)

    print(f"\n📻 Génération du lot de sweepers ({BATCH_SIZE}) — {TODAY}\n")
    index = load_index()

    fr_avoid = recent_references(index, "fr")
    en_avoid = recent_references(index, "en")

    fr_sweepers = gen_sweepers(client, "fr", BATCH_SIZE, fr_avoid)
    en_sweepers = gen_sweepers(client, "en", BATCH_SIZE, en_avoid)

    fr_clips = synth_language(fr_sweepers, "fr", VOICE_FR, OUT_FR_DIR, index)
    en_clips = synth_language(en_sweepers, "en", VOICE_EN, OUT_EN_DIR, index)

    save_index(index)

    copy_backup_clips(fr_clips, BATCH_DIR / "FR")
    copy_backup_clips(en_clips, BATCH_DIR / "EN")

    print(f"\n✅ Terminé. {len(fr_clips)} sweepers FR + {len(en_clips)} sweepers EN ajoutés.")
    print(f"   Individuels (RadioDJ) → {OUT_FR_DIR} / {OUT_EN_DIR}")
    print(f"   Historique             → {INDEX_PATH}")


if __name__ == "__main__":
    main()
