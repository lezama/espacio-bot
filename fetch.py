#!/usr/bin/env python3
"""Baja las noticias, los próximos lanzamientos y la foto del día, y los imprime como JSON para que el agente escriba el post."""

import html
import json
import os
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

POSTS = Path(__file__).parent / "_posts"
UA = {"User-Agent": "espacio-bot (https://github.com/lezama/espacio-bot)"}

NEWS_URL = "https://api.spaceflightnewsapi.net/v4/articles/?limit=20&ordering=-published_at"
LAUNCHES_URL = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=8&mode=normal"
APOD_URL = "https://api.nasa.gov/planetary/apod?api_key=" + os.environ.get("NASA_API_KEY", "DEMO_KEY")


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def article_text(url):
    """Párrafos del artículo en texto plano, para escribir desde la fuente y no desde el título. None si no se pudo leer."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            raw = r.read().decode(r.headers.get_content_charset("utf-8"), "ignore")
    except Exception:
        return None
    raw = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    paras = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<p[^>]*>(.*?)</p>", raw, flags=re.S | re.I)]
    return "\n".join(p for p in paras if len(p) > 40)[:4000] or None


def main():
    tz = ZoneInfo("America/Montevideo")
    hoy = datetime.now(tz)
    ya_contadas = [{"title": t.group(1), "source_url": u.group(1)} for f in sorted(POSTS.glob("*.md"))[-14:]
                   for s in [f.read_text()]
                   if (t := re.search(r'^title: "(.*)"$', s, flags=re.M)) and (u := re.search(r'^source_url: "(.*)"$', s, flags=re.M))]
    urls_contadas = {c["source_url"] for c in ya_contadas}

    articles = get_json(NEWS_URL)["results"]
    with ThreadPoolExecutor(8) as ex:
        texts = ex.map(lambda a: None if a["url"] in urls_contadas else article_text(a["url"]), articles)
    news = [{"title": a["title"], "source_name": a["news_site"], "source_url": a["url"],
             "published": a["published_at"][:10], "summary": a["summary"], "text": t}
            for a, t in zip(articles, texts)]

    launches = [{"net": datetime.fromisoformat(l["net"]).astimezone(tz).isoformat(), "rocket": l["name"], "where": l["pad"]["location"]["name"],
                 "mission": l["mission"]["description"] if l.get("mission") else None}
                for l in get_json(LAUNCHES_URL)["results"]
                if datetime.fromisoformat(l["net"]) > hoy][:4]

    photo = None
    try:
        apod = get_json(APOD_URL)
        if apod.get("media_type") == "image" and not apod.get("copyright"):
            photo = {"photo_url": apod["url"], "photo_title": apod["title"], "explanation": apod["explanation"]}
    except Exception as e:
        print(f"APOD no disponible: {e}", file=sys.stderr)

    json.dump({"file": f"_posts/{hoy:%Y-%m-%d}-espacio.md", "news": news, "already_told": ya_contadas,
               "launches": launches, "photo": photo}, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
