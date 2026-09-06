#!/usr/bin/env python3
"""Baja las noticias, los próximos lanzamientos y la foto del día, y los imprime como JSON para que el agente escriba el post."""

import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

POSTS = Path(__file__).parent / "_posts"
TZ = ZoneInfo("America/Montevideo")
UA = {"User-Agent": "espacio-bot (https://github.com/lezama/espacio-bot)"}

NEWS_URL = "https://api.spaceflightnewsapi.net/v4/articles/?limit=20&ordering=-published_at"
LAUNCHES_URL = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=8&mode=normal"
APOD_URL = "https://api.nasa.gov/planetary/apod?api_key=" + os.environ.get("NASA_API_KEY", "DEMO_KEY")

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def fecha_texto(dt):
    return f"{DIAS[dt.weekday()]} {dt.day} de {MESES[dt.month - 1]} de {dt.year}"


def get_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)


def article_text(url):
    """Párrafos del artículo en texto plano, para escribir desde la fuente y no desde el título."""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
            raw = r.read().decode("utf-8", "ignore")
    except Exception as e:
        return f"(no se pudo leer el artículo: {e})"
    raw = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", raw, flags=re.S | re.I)
    paras = [html.unescape(re.sub(r"<[^>]+>", "", p)).strip() for p in re.findall(r"<p[^>]*>(.*?)</p>", raw, flags=re.S | re.I)]
    return "\n".join(p for p in paras if len(p) > 40)[:4000] or "(artículo sin párrafos legibles)"


def ya_contadas():
    urls = []
    for f in sorted(POSTS.glob("*.md"))[-14:]:
        m = re.search(r'^source_url: "(.*)"$', f.read_text(), flags=re.M)
        if m:
            urls.append(m.group(1))
    return urls


def main():
    now = datetime.now(timezone.utc)
    hoy = now.astimezone(TZ)

    noticias = []
    for i, a in enumerate(get_json(NEWS_URL)["results"]):
        noticias.append({"indice": i, "titulo": a["title"], "medio": a["news_site"], "url": a["url"],
                         "publicado": a["published_at"][:10], "resumen": a["summary"], "texto": article_text(a["url"])})

    lanzamientos = []
    for l in get_json(LAUNCHES_URL)["results"]:
        net = datetime.fromisoformat(l["net"].replace("Z", "+00:00"))
        if net < now or l["status"]["abbrev"] not in ("Go", "TBC", "TBD"):
            continue
        local = net.astimezone(TZ)
        lanzamientos.append({
            "cuando": f"{fecha_texto(local)}, {local:%H:%M} hora de Uruguay",
            "cohete": l["name"],
            "empresa": l["launch_service_provider"]["name"],
            "mision": l["mission"]["description"] if l.get("mission") else "Details TBD.",
            "desde": l["pad"]["location"]["name"],
        })

    foto = None
    try:
        apod = get_json(APOD_URL)
        if apod.get("media_type") == "image" and not apod.get("copyright"):
            foto = {"url": apod["url"], "titulo": apod["title"], "explicacion": apod["explanation"]}
    except Exception as e:
        print(f"APOD no disponible: {e}", file=sys.stderr)

    json.dump({
        "archivo": f"_posts/{hoy:%Y-%m-%d}-espacio.md",
        "date": f"{hoy:%Y-%m-%d %H:%M:%S %z}",
        "fecha_texto": fecha_texto(hoy),
        "noticias": noticias,
        "ya_contadas": ya_contadas(),
        "lanzamientos": lanzamientos[:4],
        "foto": foto,
    }, sys.stdout, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
