# Hoy en el espacio

Una noticia del espacio por día. En español, sin miedo y sin inventar nada.

**Sitio:** https://lezama.github.io/espacio-bot/

## Cómo funciona

Todas las mañanas a las 7 (hora de Uruguay):

1. Un workflow abre un issue y se lo asigna al agente de GitHub Copilot.
2. El agente corre `fetch.py`, que baja las últimas noticias de la [Spaceflight News API](https://api.spaceflightnewsapi.net/v4/docs/), los próximos lanzamientos de [Launch Library](https://ll.thespacedevs.com/docs/) y la foto del día de la NASA (APOD). Las tres son JSON abierto, sin scraping.
3. Con eso y las instrucciones de [`prompt.md`](prompt.md), el agente elige una noticia, la escribe en lenguaje claro y abre un PR con un solo archivo en `_posts/`.
4. Otro workflow comprueba que el PR toca solo ese archivo y que el frontmatter es válido, y lo mergea. GitHub Pages construye el sitio con Jekyll.

Sin servidores y sin API keys: Copilot escribe, Actions publica, Pages sirve.

## Cambiar cómo escribe

Todo el criterio editorial (qué noticia elegir, tono, qué no decir, formato del post) vive en [`prompt.md`](prompt.md). Editalo y el post de mañana ya sale distinto. Lo que hace el agente paso a paso está en [`.github/copilot-instructions.md`](.github/copilot-instructions.md).

## Correr a mano

```bash
python3 fetch.py            # imprime el JSON que recibe el agente
```

En GitHub: **Actions → Pedir el post del día → Run workflow**.

## Configuración

- Secret `COPILOT_PAT`: fine-grained PAT con Issues, Pull requests, Contents y Actions en lectura y escritura sobre este repo. Lo usan los workflows para asignar el issue a Copilot y para mergear.
- Secret `NASA_API_KEY` (opcional): sin él `fetch.py` usa `DEMO_KEY`, que tiene cupo chico; si falla, el post sale sin foto.

## Licencia

MIT. Las noticias son de sus medios; las fotos del día son de la NASA y solo se muestran cuando no tienen copyright de terceros.
