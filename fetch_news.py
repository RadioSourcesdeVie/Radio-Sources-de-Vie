#!/usr/bin/env python3
import json, re, sys
from datetime import datetime
from pathlib import Path

try:
    import requests, feedparser
except ImportError:
    sys.exit("pip install requests feedparser")

TODAY = datetime.now().strftime("%Y-%m-%d")
HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120.0 Safari/537.36"}

FEEDS = {
    "chretien": [
        {"url": "https://morningstarnews.org/feed/",             "source": "Morning Star News"},
        {"url": "https://www.porteouverte.org/feed/",            "source": "Porte Ouverte"},
        {"url": "https://www.evangeliques.info/feed/",           "source": "Évangéliques Info"},
        {"url": "https://www.chretiens.info/feed/",              "source": "Chrétiens Info"},
        {"url": "https://news.google.com/rss/search?q=chr%C3%A9tien+%C3%A9glise&hl=fr", "source": "Google Actualités Chrétiennes"},
    ],
    "haiti": [
        {"url": "https://www.haitilibre.com/rss-flash.php",                         "source": "HaitiLibre"},
        {"url": "https://news.google.com/rss/search?q=Haiti&hl=fr&gl=HT&ceid=HT:fr", "source": "Google News Haiti"},
    ],
    "monde": [
        {"url": "https://feeds.bbci.co.uk/afrique/rss.xml",      "source": "BBC Afrique"},
        {"url": "https://www.france24.com/fr/rss",               "source": "France 24"},
        {"url": "https://news.un.org/feed/subscribe/fr/news/all/rss.xml", "source": "ONU Info"},
    ],
    "sport": [
        {"url": "https://news.google.com/rss/search?q=sport+football&hl=fr", "source": "Google Sport"},
        {"url": "https://news.google.com/rss/search?q=Haiti+sport&hl=fr",    "source": "Haiti Sport Google"},
    ],
}

def fetch_feed(feed_conf, max_items=5):
    items = []
    # Essai 1: requests direct
    try:
        r = requests.get(feed_conf["url"], headers=HEADERS, timeout=12)
        if r.status_code == 200:
            d = feedparser.parse(r.content)
            if d.entries:
                return parse_entries(d.entries[:max_items], feed_conf["source"])
    except Exception:
        pass
    # Essai 2: proxy RSS2JSON
    try:
        proxy = "https://api.rss2json.com/v1/api.json?rss_url=" + feed_conf["url"]
        r = requests.get(proxy, timeout=12)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "ok":
                items = []
                for item in data.get("items", [])[:max_items]:
                    desc = re.sub(r"<[^>]+>", "", item.get("description","")).strip()[:300]
                    items.append({"title": item.get("title","Sans titre"),
                        "link": item.get("link","#"), "desc": desc,
                        "date": item.get("pubDate",""), "source": feed_conf["source"]})
                return items
    except Exception:
        pass
    # Essai 3: feedparser direct
    try:
        d = feedparser.parse(feed_conf["url"])
        if d.entries:
            return parse_entries(d.entries[:max_items], feed_conf["source"])
    except Exception as e:
        print(f"  ⚠️  {feed_conf['source']}: {e}")
    return items

def parse_entries(entries, source):
    items = []
    for entry in entries:
        pub_date = ""
        if hasattr(entry,"published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6]).isoformat()
        desc = re.sub(r"<[^>]+>","",entry.get("summary","")).strip()[:300]
        items.append({"title": entry.get("title","Sans titre"),
            "link": entry.get("link","#"), "desc": desc,
            "date": pub_date, "source": source})
    return items

def main():
    all_news = {}
    total = 0
    for category, feeds in FEEDS.items():
        print(f"\n📡 {category}")
        articles = []
        for f in feeds:
            items = fetch_feed(f)
            articles.extend(items)
            total += len(items)
            print(f"  {'✅' if items else '⚠️ '} {f['source']}: {len(items)} articles")
        articles.sort(key=lambda x: x.get("date",""), reverse=True)
        all_news[category] = articles[:20]

    out_dir = Path("content/news")
    out_dir.mkdir(parents=True, exist_ok=True)
    for category, articles in all_news.items():
        out = out_dir / f"{category}_{TODAY}.json"
        out.write_text(json.dumps({"category":category,"date":TODAY,
            "updated":datetime.utcnow().isoformat()+"Z","articles":articles},
            ensure_ascii=False, indent=2), encoding="utf-8")

    Path("news_latest.json").write_text(json.dumps({
        "updated": datetime.utcnow().isoformat()+"Z",
        **{k: v[:5] for k,v in all_news.items()}
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅  {total} articles → news_latest.json")

if __name__ == "__main__":
    main()
