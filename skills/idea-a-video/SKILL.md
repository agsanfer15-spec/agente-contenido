---
name: idea-a-video
description: Convierte una idea en un guion y en un video corto vertical (TikTok, Reels, Shorts) con voz y textos en pantalla. Úsalo cuando pidan crear un video, reel o short a partir de una idea o tema.
---

# Idea → guion → video

Produce un video vertical de 720x1280 a partir de una idea, usando el paquete `agente_contenido` de este plugin. Todo el flujo es gratuito: tú (Claude) escribes el guion, la voz usa edge-tts y el montaje usa ffmpeg.

## 1. Comprueba las herramientas

```bash
ffmpeg -version | head -1
python3 -c "import edge_tts" || pip install edge-tts
```

Si falta ffmpeg, dile a la persona cómo instalarlo (`brew install ffmpeg`, `sudo apt install ffmpeg` o `winget install ffmpeg`) y para.

## 2. Escribe tú el guion

No hace falta API de pago: escribe el guion tú mismo y guárdalo como JSON en `salida/guion.json` con esta forma exacta:

```json
{
  "titulo": "máx. 60 caracteres",
  "gancho": "una frase que detenga el scroll en los primeros 3 segundos",
  "escenas": [
    {"narracion": "1-2 frases que dice la voz", "texto_pantalla": "máx. 6 palabras", "visual": "b-roll sugerido"}
  ],
  "cierre": "llamada a la acción",
  "hashtags": ["#tema"]
}
```

Reglas: español natural y frases cortas; unas 2,4 palabras por segundo de duración objetivo (60 s ≈ 145 palabras en total); entre 3 y 8 escenas; el `texto_pantalla` resume la escena, no la repite. Mira `ejemplos/guion_ejemplo.json` como referencia.

## 3. Monta el video

Desde la carpeta del plugin (`${CLAUDE_PLUGIN_ROOT}`):

```bash
cd "${CLAUDE_PLUGIN_ROOT}" && python3 -m agente_contenido --guion /ruta/a/salida/guion.json --salida /ruta/a/salida --marca "@cuenta"
```

Opciones útiles: `--voz-nombre es-ES-AlvaroNeural` (voz de España), `--voz espeak` (sin internet), `--voz ninguna` (sin voz).

## 4. Revisa antes de entregar

Saca 3 fotogramas (`ffmpeg -ss 1 -i video.mp4 -frames:v 1 f1.png`, y en la mitad y al final) y míralos: que el texto no se salga de la pantalla y se lea bien. Entrega la ruta del `.mp4` y el texto de `*.descripcion.txt` para publicar.
