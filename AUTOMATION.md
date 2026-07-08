# Cómo funciona la generación automática de CMNEWS

Este documento explica el proceso que se ejecuta **cada mañana a las 8:40 (Madrid)**,
de forma automática, sin intervención humana. No es un programa que corra en este
repositorio — es una rutina programada (un "Routine") en el sistema de Claude que,
al dispararse, resume una sesión de Claude Code y le da estas instrucciones. Este
documento es la versión legible de esa rutina; los scripts de la carpeta
[`scripts/`](./scripts) son las piezas reutilizables que esa sesión ejecuta.

## 1. Investigación

Búsqueda web extensa (15-20+ consultas) cruzando fuentes, cubriendo: geopolítica y
gobiernos, conflictos armados/defensa, economía y mercados, la competición deportiva
que esté en juego esa semana, ciencia/salud, y actualidad de España. Solo entra lo
que sería relevante para alguien informado y ocupado — nada de relleno.

## 2. Contenido

- **Web** (`https://claude.ai/code/artifact/7019ef44-7def-4a79-94c2-2a8b6c6eeaad`):
  HTML con el mismo sistema de diseño de siempre (masthead, ticker de mercados,
  portada, secciones en rejilla, caja de calendario).
- **Podcast**: guion en español de ~1500 palabras/~10 minutos, sin referencias
  personales (es contenido para cualquier oyente). "CMNEWS" se escribe "Si, Em, News"
  en el guion hablado para que la voz lo pronuncie bien; en la web y el feed sigue
  siendo "CMNEWS" como texto.

## 3. Generación de audio — `scripts/generate_podcast_audio.py`

El guion se divide en trozos de 1-2 frases (nunca una frase muy corta sola en la
intro/despedida, que es donde peor suena). Cada trozo se genera por separado con la
API de ElevenLabs (voz "Victor", español de España) y se normaliza individualmente
a -16 LUFS antes de concatenar — generar el episodio entero en una sola llamada
hace que el modelo de voz pierda volumen a mitad de camino, así que trocear es
obligatorio.

```
ELEVENLABS_API_KEY=... python3 scripts/generate_podcast_audio.py guion.txt episodio.mp3
```

## 4. Verificación por subagentes (antes de publicar)

Tres subagentes de Claude revisan el trabajo antes de que se publique nada:

- **Subagente A — volumen**: mide el nivel LUFS de cada trozo de audio y marca
  cualquiera que se desvíe de la mediana; los trozos marcados se regeneran hasta
  2 veces.
- **Subagente B — entonación de intro/despedida**: se generan 3 variantes de la
  primera y la última frase del guion (las que peor suelen sonar), y el subagente
  elige la más natural de cada una comparando nivel y cortes/silencios anómalos.
- **Subagente C — supervisor final**: tras publicar, comprueba que la web tiene la
  fecha de hoy, que el episodio nuevo está accesible (HTTP 200) con el tamaño
  correcto, y que el feed es XML válido. Si encuentra un problema, se arregla y se
  vuelve a comprobar antes de dar la tarea por terminada.

## 5. Publicación

- El audio final se guarda en `episodes/DD-MM-AAAA.mp3` y se añade una entrada nueva
  al principio de `feed.xml` (los episodios anteriores nunca se borran).
- Si el nombre de un archivo ya existía antes (por ejemplo al corregir un episodio
  del mismo día), se le añade un sufijo (`-v2`, `-v3`...) en vez de sobrescribir la
  misma URL — Spotify y otros clientes cachean por URL, así que reutilizar la misma
  URL para contenido distinto no siempre provoca una redescarga.
- Se revisa el calendario de Google por si hay algún evento mundial de primer nivel
  que marcar, y se deja un borrador (no enviado) en Gmail con el titular del día.

## Seguridad

La clave de API de ElevenLabs **no está en este repositorio** (es público). Vive
únicamente dentro de la rutina automática privada. Si ejecutas `generate_podcast_audio.py`
tú mismo, pásala como variable de entorno, nunca la escribas en un fichero que vaya
a subirse aquí.
