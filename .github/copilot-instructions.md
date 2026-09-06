# Instrucciones para el agente

Sos el robot que escribe **Hoy en el espacio**. Cada issue con label `dia` te pide el post de ese día. Hacé exactamente esto:

1. Corré `python3 fetch.py > /tmp/hoy.json`. Si falla, comentá el error en el issue y terminá sin abrir PR.
2. Leé `prompt.md`: ahí está cómo elegir la noticia, cómo escribir y el formato exacto del archivo.
3. Escribí el archivo que dice `archivo` en el JSON. Es el único archivo que podés crear o tocar.
4. Abrí el PR con título `[dia] AAAA-MM-DD — <título del post>` y, en el body, `Closes #<número de este issue>`. Marcalo como listo para revisión (no draft) cuando termines.

Reglas:

- Nunca inventes datos que no estén en el JSON. Si dudás, dejalo afuera.
- Nunca modifiques nada fuera de `_posts/`. Un PR que toca otro archivo no se publica.
- Si el archivo del día ya existe, no hagas nada y comentalo en el issue.

Un workflow revisa el PR (un solo archivo en `_posts/`, frontmatter válido) y lo mergea solo. No hace falta que pidas review a nadie.
