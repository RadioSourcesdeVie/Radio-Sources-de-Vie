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
        {"url": "https://morningstarnews.org/feed/",             "source": "Morning Star News", "lang": "en"},
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
                return parse_entries(d.entries[:max_items], feed_conf["source"],
                                 feed_conf.get("lang", "fr"))
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
                        "date": item.get("pubDate",""), "source": feed_conf["source"],
                        "lang": feed_conf.get("lang", "fr")})
                return items
    except Exception:
        pass
    # Essai 3: feedparser direct
    try:
        d = feedparser.parse(feed_conf["url"])
        if d.entries:
            return parse_entries(d.entries[:max_items], feed_conf["source"],
                                 feed_conf.get("lang", "fr"))
    except Exception as e:
        print(f"  ⚠️  {feed_conf['source']}: {e}")
    return items

def parse_entries(entries, source, lang="fr"):
    items = []
    for entry in entries:
        pub_date = ""
        if hasattr(entry,"published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6]).isoformat()
        desc = re.sub(r"<[^>]+>","",entry.get("summary","")).strip()[:300]
        items.append({"title": entry.get("title","Sans titre"),
            "link": entry.get("link","#"), "desc": desc,
            "date": pub_date, "source": source, "lang": lang})
    return items

ANGLAIS = re.compile(
    r"\b(the|and|with|from|after|says|said|against|among|killed|attack|"
    r"church|christian|children|police|court|report|government|people|"
    r"years|leader|death|sentenced|building|threatened|home|faith)\b",
    re.IGNORECASE,
)


def semble_anglais(article):
    """Filet, pour l'article anglais isole dans un flux francophone."""
    texte = f"{article.get('title','')} {article.get('desc','')}"
    if not texte.strip():
        return False
    anglais = len(set(m.lower() for m in ANGLAIS.findall(texte)))
    accents = sum(texte.count(c) for c in "éèêëàâçùûîïôœ")
    return anglais >= 3 and accents <= 1


def traduire(articles, cle):
    """
    Traduit en francais les articles qui n'y sont pas.

    Tout ce qui sort d'ici part sur le site, dans le journal du soir et
    dans les flux RSS. Un titre anglais sur une radio francophone est
    une faute visible : si la traduction echoue, on ECARTE l'article
    plutot que de le publier tel quel.

    Renvoie la liste gardee.
    """
    a_faire = [a for a in articles
               if a.get("lang") == "en" or semble_anglais(a)]
    if not a_faire:
        return articles
    if not cle:
        print(f"  ⚠️  {len(a_faire)} articles en anglais écartés (pas de clé API)")
        return [a for a in articles if a not in a_faire]

    try:
        import anthropic
    except ImportError:
        print(f"  ⚠️  {len(a_faire)} articles en anglais écartés (anthropic absent)")
        return [a for a in articles if a not in a_faire]

    lot = [{"i": i, "titre": a.get("title", ""), "resume": a.get("desc", "")}
           for i, a in enumerate(a_faire)]
    prompt = (
        "Traduis en francais ces titres et resumes de depeches, pour une "
        "radio chretienne francophone.\n\n"
        "Garde le ton d'une depeche : sobre, factuel, pas de commentaire. "
        "Conserve les noms propres, les lieux et les chiffres tels quels. "
        "Ne raccourcis pas, ne resume pas, ne rajoute rien.\n\n"
        f"{json.dumps(lot, ensure_ascii=False, indent=1)}\n\n"
        "Reponds UNIQUEMENT par un tableau JSON de la meme longueur et dans "
        'le meme ordre : [{"i": 0, "titre": "...", "resume": "..."}, ...]'
    )
    try:
        client = anthropic.Anthropic(api_key=cle)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001", max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )
        brut = msg.content[0].text.strip()
        if "```" in brut:
            brut = brut.split("```")[1]
            if brut.startswith("json"):
                brut = brut[4:]
        d, f = brut.find("["), brut.rfind("]")
        traductions = json.loads(brut[d:f + 1])
        par_indice = {int(x["i"]): x for x in traductions}
        if len(par_indice) != len(a_faire):
            raise ValueError(
                f"{len(par_indice)} traductions pour {len(a_faire)} articles")
        for i, a in enumerate(a_faire):
            tr = par_indice[i]
            a["title"] = tr.get("titre") or a["title"]
            a["desc"] = tr.get("resume") or a.get("desc", "")
            a["lang"] = "fr"
            a["traduit_de"] = "en"
        print(f"  🌍 {len(a_faire)} articles traduits de l'anglais")
        return articles
    except Exception as e:
        print(f"  ⚠️  traduction impossible ({e}) — {len(a_faire)} articles écartés")
        return [a for a in articles if a not in a_faire]


def main():
    import argparse, os
    ap = argparse.ArgumentParser()
    ap.add_argument("--api-key", default=os.environ.get("ANTHROPIC_KEY", ""))
    cle = ap.parse_args().api_key

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
        articles = traduire(articles, cle)
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
