# Agente de contenido

Convierte una **idea** en un **guion** y en un **video corto vertical** (720x1280, listo para TikTok, Reels y Shorts) con voz, textos grandes en pantalla, fondo animado y barra de progreso.

```
idea ──► guion (IA) ──► voz (edge-tts) ──► montaje (ffmpeg) ──► video.mp4 + descripción
```

Todo puede funcionar **gratis**: la voz usa edge-tts, el montaje usa ffmpeg y el guion lo puede escribir Claude Code (sin API), un modelo local con Ollama o tú mismo.

## Instalación

Necesitas Python 3.9+ y ffmpeg.

```bash
# ffmpeg
brew install ffmpeg            # macOS
sudo apt install ffmpeg        # Ubuntu/Debian
winget install ffmpeg          # Windows

# el agente
git clone https://github.com/agsanfer15-spec/agente-contenido
cd agente-contenido
pip install -e .               # añade ".[claude]" si vas a usar la API de Claude
```

## Uso rápido

**Con un guion ya escrito (gratis, sin IA):**

```bash
agente-contenido --guion ejemplos/guion_ejemplo.json --marca "@tucuenta"
```

**De idea a video con Ollama (gratis, local):**

```bash
ollama pull llama3.1
agente-contenido "3 hábitos para ahorrar sin darte cuenta" --motor-guion ollama
```

**De idea a video con la API de Claude (de pago):**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
agente-contenido "3 hábitos para ahorrar sin darte cuenta" --duracion 60
```

El resultado queda en `salida/`:

| Archivo | Qué es |
|---|---|
| `<titulo>.mp4` | El video vertical con voz |
| `<titulo>.guion.json` | El guion, para editarlo y volver a montar con `--guion` |
| `<titulo>.descripcion.txt` | Título, gancho, cierre y hashtags para copiar al publicar |

## Opciones

| Opción | Por defecto | Para qué |
|---|---|---|
| `--motor-guion claude\|ollama` | `claude` | Quién escribe el guion |
| `--modelo` | `claude-sonnet-5-5` / `llama3.1` | Modelo concreto |
| `--duracion` | `60` | Segundos objetivo |
| `--tono` | `cercano y enérgico` | Estilo del guion |
| `--voz edge\|espeak\|ninguna` | `edge` | Voz neuronal gratis (internet), voz offline, o sin voz |
| `--voz-nombre` | `es-MX-JorgeNeural` | Otras: `es-ES-AlvaroNeural`, `es-ES-ElviraNeural`, `es-MX-DaliaNeural` |
| `--marca` | (vacío) | Texto arriba, p. ej. `@tucuenta` |
| `--solo-guion` | | Solo imprime el guion en JSON |
| `--salida` | `salida/` | Carpeta de salida |

## Como plugin de Claude Code

Este repositorio también es un plugin. Dentro de Claude Code:

```
/plugin marketplace add agsanfer15-spec/agente-contenido
/plugin install agente-contenido@agente-contenido
```

Luego pide «hazme un video sobre …» o usa `/agente-contenido:video <idea>`. Claude escribe el guion él mismo (sin API de pago) y monta el video con este paquete.

## Usarlo desde Python

```python
from pathlib import Path
from agente_contenido import idea_a_video

r = idea_a_video("Cómo hacer café de especialidad en casa", Path("salida"), motor_guion="ollama")
print(r.video, r.duracion)
```

## Formato del guion

```json
{
  "titulo": "3 hábitos para ahorrar sin darte cuenta",
  "gancho": "¿Y si te digo que puedes ahorrar sin sentir que te privas de nada?",
  "escenas": [
    {"narracion": "Hábito uno: págate primero…", "texto_pantalla": "1. Págate primero", "visual": "…"}
  ],
  "cierre": "Guarda este video y sígueme para más trucos.",
  "hashtags": ["#ahorro"]
}
```

Ejemplo completo en [`ejemplos/guion_ejemplo.json`](ejemplos/guion_ejemplo.json).

## Pruebas

```bash
pip install -e ".[dev]"
pytest
```

## Estructura

```
agente_contenido/
  guion.py    # idea → guion (Claude u Ollama)
  voz.py      # narración → audio (edge-tts, espeak-ng o silencio)
  video.py    # bloques → clips 720x1280 → MP4 con ffmpeg
  agente.py   # orquestador
  cli.py      # línea de comandos
.claude-plugin/  skills/  commands/   # empaquetado como plugin de Claude Code
ejemplos/   tests/
```
