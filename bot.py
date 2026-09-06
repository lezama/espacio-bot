#!/usr/bin/env python3
"""Escribe el post del día: tres fuentes JSON, una llamada a Claude, un archivo en _posts/."""

import argparse
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import anthropic
from pydantic import BaseModel

ROOT = Path(__file__).parent
POSTS = ROOT / "_posts"
TZ = ZoneInfo("America/Montevideo")
UA = {"User-Agent": "espacio-bot (https://github.com/lezama/espacio-bot)"}

NEWS_URL = "https://api.spaceflightnewsapi.net/v4/articles/?limit=20&ordering=-published_at"
LAUNCHES_URL = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=8&mode=normal"
APOD_URL = "https://api.nasa.gov/planetary/apod?api_key=" + os.environ.get("NASA_API_KEY", "DEMO_KEY")

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


class Palabra(BaseModel):
    palabra: str
    significado: str


class Lanzamiento(BaseModel):
    indice: int
    que_es: str


class Post(BaseModel):
    titulo: str
    fuente_indice: int
    noticia_md: str
    por_que_importa: str
    palabras_nuevas: list[Palabra]
    lanzamientos: list[Lanzamiento]
    foto_epigrafe: str


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
    text = "\n".join(p for p in paras if len(p) > 40)
    return text[:4000] or "(artículo sin párrafos legibles)"


def ya_contadas():
    urls = []
    for f in sorted(POSTS.glob("*.md"))[-14:]:
        m = re.search(r'^source_url: "(.*)"$', f.read_text(), flags=re.M)
        if m:
            urls.append(m.group(1))
    return urls


def fetch_all(now):
    news = get_json(NEWS_URL)["results"]
    for a in news:
        a["texto"] = article_text(a["url"])

    launches = []
    for l in get_json(LAUNCHES_URL)["results"]:
        net = datetime.fromisoformat(l["net"].replace("Z", "+00:00"))
        if net < now or l["status"]["abbrev"] not in ("Go", "TBC", "TBD"):
            continue
        local = net.astimezone(TZ)
        launches.append({
            "cuando": f"{fecha_texto(local)}, {local:%H:%M} hora de Uruguay",
            "cohete": l["name"],
            "empresa": l["launch_service_provider"]["name"],
            "mision": l["mission"]["description"] if l.get("mission") else "Details TBD.",
            "desde": l["pad"]["location"]["name"],
        })
    launches = launches[:4]

    foto = None
    try:
        apod = get_json(APOD_URL)
        if apod.get("media_type") == "image" and not apod.get("copyright"):
            foto = {"url": apod["url"], "titulo": apod["title"], "explicacion": apod["explanation"]}
    except Exception as e:
        print(f"APOD no disponible: {e}", file=sys.stderr)

    return news, launches, foto


def escribir(news, launches, foto, hoy):
    entrada = {
        "hoy": fecha_texto(hoy),
        "noticias": [{"indice": i, "titulo": a["title"], "medio": a["news_site"], "url": a["url"],
                      "publicado": a["published_at"][:10], "resumen": a["summary"], "texto": a["texto"]}
                     for i, a in enumerate(news)],
        "ya_contadas": ya_contadas(),
        "lanzamientos": [{"indice": i, **l} for i, l in enumerate(launches)],
        "foto": foto,
    }
    client = anthropic.Anthropic()
    response = client.messages.parse(
        model="claude-opus-5",
        max_tokens=16000,
        system=(ROOT / "prompt.md").read_text(),
        messages=[{"role": "user", "content": json.dumps(entrada, ensure_ascii=False)}],
        output_format=Post,
    )
    if response.stop_reason != "end_turn":
        sys.exit(f"el modelo terminó con stop_reason={response.stop_reason}")
    return response.parsed_output


def render(post, news, launches, foto, hoy):
    q = lambda s: json.dumps(s, ensure_ascii=False)
    fuente = news[post.fuente_indice]
    fm = [
        "---",
        f"title: {q(post.titulo)}",
        f"date: {hoy:%Y-%m-%d %H:%M:%S %z}",
        f"fecha_texto: {q(fecha_texto(hoy))}",
        f"source_url: {q(fuente['url'])}",
        f"source_name: {q(fuente['news_site'])}",
    ]
    if foto and post.foto_epigrafe:
        fm += [f"photo_url: {q(foto['url'])}", f"photo_title: {q(foto['titulo'])}", f"photo_caption: {q(post.foto_epigrafe)}"]
    if post.lanzamientos:
        fm.append("launches:")
        for l in post.lanzamientos:
            src = launches[l.indice]
            fm += [f"  - when: {q(src['cuando'])}", f"    rocket: {q(src['cohete'])}", f"    where: {q(src['desde'])}", f"    what: {q(l.que_es)}"]
    fm.append("---")

    body = [post.noticia_md.strip(), "", "## ¿Por qué importa?", "", post.por_que_importa.strip()]
    if post.palabras_nuevas:
        body += ["", "## Palabras nuevas", ""] + [f"- **{p.palabra}**: {p.significado}" for p in post.palabras_nuevas]
    return "\n".join(fm + [""] + body) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="solo fetchea y muestra lo que recibiría el modelo")
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    hoy = now.astimezone(TZ)
    out = POSTS / f"{hoy:%Y-%m-%d}-espacio.md"
    if out.exists() and not args.dry_run:
        print(f"{out.name} ya existe, nada que hacer")
        return

    news, launches, foto = fetch_all(now)
    if args.dry_run:
        print(json.dumps({"noticias": [(a["title"], len(a["texto"])) for a in news], "lanzamientos": launches,
                          "foto": foto and foto["titulo"], "ya_contadas": ya_contadas()}, ensure_ascii=False, indent=2))
        return

    post = escribir(news, launches, foto, hoy)
    out.write_text(render(post, news, launches, foto, hoy))
    print(f"escrito {out}")


if __name__ == "__main__":
    main()
