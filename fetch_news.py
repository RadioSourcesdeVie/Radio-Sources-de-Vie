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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# Proxy RSS2JSON qui contourne les blocages réseau
RSS2JSON = "https://api.rss2json.com/v1/api.json?rss_url="

FEEDS = {
    "chretien": [
        {"url": "https://www.crosswalk.com/rss/",                          "source": "Crosswalk"},
        {"url": "https://www.thegospelcoalition.org/feed/",                "source": "Gospel Coalition"},
        {"url": "https://www.christianitytoday.com/ct/rss.xml",           "source": "Christianity Today"},
    ],
    "haiti": [
        {"url": "https://www.haitilibre.com/rssfeed.php",                  "source": "Haiti Libre"},
        {"url": "https://www.haitiantimes.com/feed/",                      "source": "Haitian Times"},
        {"url": "https://ayibopost.com/feed/",                             "source": "Ayibo Post"},
    ],
    "monde": [
        {"url": "https://feeds.bbci.co.uk/afrique/rss.xml",               "source": "BBC Afrique"},
        {"url": "https://www.france24.com/fr/rss",                        "source": "France 24"},
        {"url": "https://www.voanews.com/api/zyrqmveitmqt",               "source": "VOA Afrique"},
    ],
}

def fetch_via_proxy(feed_conf, max_items=5):
    """Essaie d'abord direct, puis via proxy RSS2JSON."""
    items = []
    
    # Essai 1: direct avec requests
    try:
        r = requests.get(feed_conf["url"], headers=HEADERS, timeout=10)
        if r.status_code == 200:
            d = feedparser.parse(r.content)
            if d.entries:
                return parse_feedparser(d, feed_conf["source"], max_items)
    except Exception:
        pass
    
    # Essai 2: via proxy RSS2JSON
    try:
        proxy_url = RSS2JSON + feed_conf["url"]
        r = requests.get(proxy_url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("status") == "ok":
                for item in data.get("items", [])[:max_items]:
                    desc = re.sub(r"<[^>]+>", "", item.get("description","")).strip()[:300]
                    items.append({
                        "title":  item.get("title", "Sans titre"),
                        "link":   item.get("link", "#"),
                        "desc":   desc,
                        "date":   item.get("pubDate", ""),
                        "source": feed_conf["source"],
                    })
                return items
    except Exception:
        pass
    
    # Essai 3: feedparser direct (fallback)
    try:
        d = feedparser.parse(feed_conf["url"])
        if d.entries:
            return parse_feedparser(d, feed_conf["source"], max_items)
    except Exception as e:
        print(f"  ⚠️  {feed_conf['source']}: {e}")
    
    return items

def parse_feedparser(d, source, max_items):
    items = []
    for entry in d.entries[:max_items]:
        pub_date = ""
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6]).isoformat()
        desc = re.sub(r"<[^>]+>", "", entry.get("summary","")).strip()[:300]
        items.append({
            "title":  entry.get("title", "Sans titre"),
            "link":   entry.get("link", "#"),
            "desc":   desc,
            "date":   pub_date,
            "source": source,
        })
    return items

def main():
    all_news = {}
    total = 0
    for category, feeds in FEEDS.items():
        print(f"\n📡 {category}")
        articles = []
        for f in feeds:
            items = fetch_via_proxy(f)
            articles.extend(items)
            total += len(items)
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
    print(f"\n✅  {total} articles au total → news_latest.json")

if __name__ == "__main__":
    main()
