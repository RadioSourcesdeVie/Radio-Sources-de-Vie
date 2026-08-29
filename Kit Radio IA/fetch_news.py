#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kit Radio IA - Récupération des flux RSS par catégorie (config.CATEGORIES_NEWS)
Sauvegarde content/news/{categorie}_{date}.json et news_latest.json.
Usage : python fetch_news.py
"""
import sys
import re
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import config

import requests
import feedparser

TODAY = datetime.now().strftime("%Y-%m-%d")
BASE_DIR = Path(__file__).parent.parent
HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120.0 Safari/537.36"}


def parse_entries(entries, source, max_items):
    items = []
    for entry in entries[:max_items]:
        pub_date = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6]).isoformat()
        desc = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()[:300]
        items.append({"title": entry.get("title", "Sans titre"), "link": entry.get("link", "#"),
                      "desc": desc, "date": pub_date, "source": source})
    return items


def fetch_feed(feed_conf: dict, max_items: int = 5) -> list:
    url, source = feed_conf["url"], feed_conf["source"]
    # 1) requests direct
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            d = feedparser.parse(r.content)
            if d.entries:
                return parse_entries(d.entries, source, max_items)
    except Exception:
        pass
    # 2) proxy RSS2JSON (contourne certains blocages anti-bot)
    try:
        proxy = "https://api.rss2json.com/v1/api.json?rss_url=" + url
        r = requests.get(proxy, timeout=12)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "ok":
                items = []
                for item in data.get("items", [])[:max_items]:
                    desc = re.sub(r"<[^>]+>", "", item.get("description", "")).strip()[:300]
                    items.append({"title": item.get("title", "Sans titre"), "link": item.get("link", "#"),
                                  "desc": desc, "date": item.get("pubDate", ""), "source": source})
                return items
    except Exception:
        pass
    # 3) feedparser direct
    try:
        d = feedparser.parse(url)
        if d.entries:
            return parse_entries(d.entries, source, max_items)
    except Exception as e:
        print(f"    erreur {source}: {e}")
    return []


def main():
    all_news = {}
    total = 0
    for cle, cat in config.CATEGORIES_NEWS.items():
        print(f"\n{cat['label']} ({cle})")
        articles = []
        for feed_conf in cat["flux"]:
            items = fetch_feed(feed_conf)
            articles.extend(items)
            total += len(items)
            print(f"  {'OK' if items else '--'}  {feed_conf['source']}: {len(items)} articles")
        articles.sort(key=lambda x: x.get("date", ""), reverse=True)
        all_news[cle] = articles[:20]

    out_dir = BASE_DIR / "content" / "news"
    out_dir.mkdir(parents=True, exist_ok=True)
    for cle, articles in all_news.items():
        out = out_dir / f"{cle}_{TODAY}.json"
        out.write_text(json.dumps({"category": cle, "date": TODAY,
                                    "updated": datetime.utcnow().isoformat() + "Z", "articles": articles},
                                   ensure_ascii=False, indent=2), encoding="utf-8")

    (BASE_DIR / "news_latest.json").write_text(json.dumps({
        "updated": datetime.utcnow().isoformat() + "Z",
        **{k: v[:5] for k, v in all_news.items()}
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{total} articles -> news_latest.json")


if __name__ == "__main__":
    main()
