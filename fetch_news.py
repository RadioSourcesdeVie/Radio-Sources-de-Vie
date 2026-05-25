#!/usr/bin/env python3
import json, re, sys
from datetime import datetime
from pathlib import Path

try:
    import requests, feedparser
except ImportError:
    sys.exit("pip install requests feedparser")

TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

FEEDS = {
    "chretien": [
        {"url": "https://www.christianpost.com/rss/all",    "source": "Christian Post"},
        {"url": "https://www.crosswalk.com/rss/",           "source": "Crosswalk"},
    ],
    "haiti": [
        {"url": "https://www.loophaiti.com/feed/",          "source": "Loop Haïti"},
        {"url": "https://www.alterpresse.org/rss.php",      "source": "AlterPresse"},
    ],
    "monde": [
        {"url": "https://rss.rfi.fr/rfi/francais",          "source": "RFI"},
        {"url": "https://feeds.bbci.co.uk/afrique/rss.xml", "source": "BBC Afrique"},
    ],
}

def fetch_feed(feed_conf, max_items=5):
    items = []
    try:
        r = requests.get(feed_conf["url"], headers=HEADERS, timeout=15)
        r.raise_for_status()
        d = feedparser.parse(r.content)
        for entry in d.entries[:max_items]:
            pub_date = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6]).isoformat()
            desc = re.sub(r"<[^>]+>", "", entry.get("summary", "")).strip()[:300]
            items.append({
                "title":  entry.get("title", "Sans titre"),
                "link":   entry.get("link", "#"),
                "desc":   desc,
                "date":   pub_date,
                "source": feed_conf["source"],
            })
    except Exception as e:
        print(f"  ⚠️  {feed_conf['source']}: {e}")
    return items

def main():
    all_news = {}
    for category, feeds in FEEDS.items():
        print(f"\n📡 {category}")
        articles = []
        for f in feeds:
            items = fetch_feed(f)
            articles.extend(items)
            print(f"  {'✅' if items else '⚠️ '} {f['source']}: {len(items)} articles")
        articles.sort(key=lambda x: x.get("date",""), reverse=True)
        all_news[category] = articles[:20]

    out_dir = Path("content/news")
    out_dir.mkdir(parents=True, exist_ok=True)
    for category, articles in all_news.items():
        out = out_dir / f"{category}_{TODAY}.json"
        out.write_text(json.dumps({
            "category": category, "date": TODAY,
            "updated": datetime.utcnow().isoformat()+"Z",
            "articles": articles
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    Path("news_latest.json").write_text(json.dumps({
        "updated": datetime.utcnow().isoformat()+"Z",
        **{k: v[:5] for k,v in all_news.items()}
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅  news_latest.json mis à jour")

if __name__ == "__main__":
    main()
