# Hoy en el espacio

Una noticia del espacio por día, contada para niñas de 8 a 12 años. En español, sin miedo y sin inventar nada.

**Sitio:** https://lezama.github.io/espacio-bot/

## Cómo funciona

Todas las mañanas a las 7 (hora de Uruguay) un workflow de GitHub Actions corre `bot.py`, que:

1. Baja las últimas noticias de la [Spaceflight News API](https://api.spaceflightnewsapi.net/v4/docs/), los próximos lanzamientos de [Launch Library](https://ll.thespacedevs.com/docs/) y la foto del día de la NASA (APOD). Las tres son JSON abierto, sin scraping.
2. Le pasa todo eso a Claude con las instrucciones de [`prompt.md`](prompt.md) y recibe una noticia elegida y escrita para niñas, con glosario y una línea por lanzamiento.
3. Escribe `_posts/AAAA-MM-DD-espacio.md` y lo commitea a `main`. GitHub Pages construye el sitio con Jekyll.

No hay agente, no hay servidores, no hay PRs: un script, una llamada al modelo, un commit.

## Cambiar cómo escribe

Todo el criterio editorial (qué noticia elegir, tono, qué no decir) vive en [`prompt.md`](prompt.md). Editalo y el post de mañana ya sale distinto.

## Correr a mano

```bash
pip install anthropic
python bot.py --dry-run          # muestra qué recibiría el modelo, sin llamarlo
ANTHROPIC_API_KEY=... python bot.py   # escribe el post de hoy (si ya existe, borralo primero)
```

En GitHub: **Actions → Post del día → Run workflow**.

## Secrets

- `ANTHROPIC_API_KEY` (obligatorio).
- `NASA_API_KEY` (opcional; sin él usa `DEMO_KEY`, que tiene cupo chico y a veces falla, y entonces el post sale sin foto).

## Licencia

MIT. Las noticias son de sus medios; las fotos del día son de la NASA y solo se muestran cuando no tienen copyright de terceros.
