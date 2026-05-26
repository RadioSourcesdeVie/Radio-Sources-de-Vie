#!/usr/bin/env python3
"""
generate_rss.py — Génère les flux RSS pour RadioDJ
Radio Sources de Vie Chrétienne
"""
import json
from datetime import datetime
from pathlib import Path

BASE_URL = "https://www.radiosourcesdevie.org"
TODAY = datetime.now().strftime("%Y-%m-%d")
NOW_RFC = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

SEGMENTS = [
    {
        "key": "prayer_matin",
        "title": "Prière du Matin — Radio Sources de Vie",
        "description": "Prière quotidienne du matin — Voix Bella",
        "json_path": f"content/prayers/matin_{TODAY}.json",
        "mp3_path":  f"audio/prayers/matin_{TODAY}.mp3",
    },
    {
        "key": "prayer_soir",
        "title": "Prière du Soir — Radio Sources de Vie",
        "description": "Prière quotidienne du soir — Voix Bella",
        "json_path": f"content/prayers/soir_{TODAY}.json",
        "mp3_path":  f"audio/prayers/soir_{TODAY}.mp3",
    },
    {
        "key": "testimony",
        "title": "Témoignage — Radio Sources de Vie",
        "description": "Témoignage chrétien quotidien — Voix Elli",
        "json_path": f"content/testimonies/{TODAY}.json",
        "mp3_path":  f"audio/testimonies/{TODAY}.mp3",
    },
    {
        "key": "sabbat",
        "title": "Sabbat School Nugget — Radio Sources de Vie",
        "description": "Leçon de l'École du Sabbat — Voix Antoni",
        "json_path": f"content/sabbat/{TODAY}.json",
        "mp3_path":  f"audio/sabbat/{TODAY}.mp3",
    },
    {
        "key": "meteo",
        "title": "Météo Ottawa & Port-au-Prince — Radio Sources de Vie",
        "description": "Météo quotidienne Ottawa et Port-au-Prince — Voix Bella",
        "json_path": f"content/meteo/{TODAY}.json",
        "mp3_path":  f"audio/meteo/{TODAY}.mp3",
    },
    {
        "key": "resume_chretien",
        "title": "Résumé Nouvelles Chrétiennes — Radio Sources de Vie",
        "description": "Résumé des nouvelles chrétiennes — Voix Charlotte",
        "json_path": f"content/resumes/chretien_{TODAY}.json",
        "mp3_path":  f"audio/resumes/chretien_{TODAY}.mp3",
    },
    {
        "key": "resume_haiti",
        "title": "Résumé Nouvelles Haïti — Radio Sources de Vie",
        "description": "Résumé des nouvelles d'Haïti — Voix Charlotte",
        "json_path": f"content/resumes/haiti_{TODAY}.json",
        "mp3_path":  f"audio/resumes/haiti_{TODAY}.mp3",
    },
    {
        "key": "resume_monde",
        "title": "Résumé Nouvelles Internationales — Radio Sources de Vie",
        "description": "Résumé des nouvelles internationales — Voix Charlotte",
        "json_path": f"content/resumes/monde_{TODAY}.json",
        "mp3_path":  f"audio/resumes/monde_{TODAY}.mp3",
    },
    {
        "key": "resume_sport",
        "title": "Résumé Sport — Radio Sources de Vie",
        "description": "Résumé sportif du jour — Voix Charlotte",
        "json_path": f"content/resumes/sport_{TODAY}.json",
        "mp3_path":  f"audio/resumes/sport_{TODAY}.mp3",
    },
]

def get_title(json_path):
    try:
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        return data.get("title") or data.get("name") or "Sans titre"
    except:
        return "Sans titre"

def get_size(mp3_path):
    try:
        return Path(mp3_path).stat().st_size
    except:
        return 0

def make_rss(segment):
    title = get_title(segment["json_path"])
    mp3_url = f"{BASE_URL}/{segment['mp3_path']}"
    size = get_size(segment["mp3_path"])
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>{segment['title']}</title>
    <description>{segment['description']}</description>
    <link>{BASE_URL}</link>
    <language>fr</language>
    <lastBuildDate>{NOW_RFC}</lastBuildDate>
    <itunes:author>Radio Sources de Vie Chrétienne</itunes:author>
    <itunes:category text="Religion &amp; Spirituality"/>
    <item>
      <title>{title}</title>
      <description>{segment['description']} — {TODAY}</description>
      <pubDate>{NOW_RFC}</pubDate>
      <enclosure url="{mp3_url}" length="{size}" type="audio/mpeg"/>
      <guid>{mp3_url}</guid>
      <itunes:duration>00:01:00</itunes:duration>
    </item>
  </channel>
</rss>"""

# Créer dossier RSS
rss_dir = Path("rss")
rss_dir.mkdir(exist_ok=True)

print(f"\n📡 Génération flux RSS — {TODAY}\n")
for seg in SEGMENTS:
    rss_content = make_rss(seg)
    rss_file = rss_dir / f"{seg['key']}.xml"
    rss_file.write_text(rss_content, encoding="utf-8")
    mp3_exists = Path(seg['mp3_path']).exists()
    print(f"{'✅' if mp3_exists else '⚠️ '} {seg['key']}: {BASE_URL}/rss/{seg['key']}.xml")

# Index RSS global
index = {
    "radio": "Radio Sources de Vie Chrétienne",
    "base_url": BASE_URL,
    "updated": TODAY,
    "feeds": {seg['key']: f"{BASE_URL}/rss/{seg['key']}.xml" for seg in SEGMENTS}
}
Path("rss/index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n📋 Index RSS: {BASE_URL}/rss/index.json")
print(f"\n✅ {len(SEGMENTS)} flux RSS générés!")
