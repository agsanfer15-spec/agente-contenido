"""Paso 2: convertir la narración de cada bloque en audio.

Motores disponibles:
- "edge"   : voces neuronales gratuitas de Microsoft (paquete edge-tts, necesita internet).
- "espeak" : espeak-ng, totalmente offline, voz robótica.
- "ninguna": sin voz; cada bloque dura según su número de palabras (útil para subtitular a mano).
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

VOZ_POR_DEFECTO = "es-MX-JorgeNeural"
PALABRAS_POR_SEGUNDO = 2.4


def duracion_audio(ruta: Path) -> float:
    salida = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(salida)


def duracion_estimada(texto: str) -> float:
    return max(2.0, len(texto.split()) / PALABRAS_POR_SEGUNDO + 0.4)


def _silencio(ruta: Path, segundos: float) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-t", f"{segundos:.2f}", "-c:a", "pcm_s16le", str(ruta)],
        check=True,
    )


def _edge(texto: str, ruta_mp3: Path, voz: str) -> None:
    import edge_tts

    asyncio.run(edge_tts.Communicate(texto, voz).save(str(ruta_mp3)))


def _espeak(texto: str, ruta_wav: Path) -> None:
    binario = shutil.which("espeak-ng") or shutil.which("espeak")
    if not binario:
        raise RuntimeError("No se encontró espeak-ng. Instálalo o usa --voz edge / ninguna.")
    subprocess.run([binario, "-v", "es-419", "-s", "165", "-w", str(ruta_wav), texto], check=True)


def sintetizar(texto: str, destino: Path, motor: str = "edge", voz: str = VOZ_POR_DEFECTO) -> Path:
    """Genera un WAV para `texto` en `destino` (sin extensión) y devuelve su ruta."""
    wav = destino.with_suffix(".wav")
    if motor == "ninguna":
        _silencio(wav, duracion_estimada(texto))
        return wav
    if motor == "edge":
        mp3 = destino.with_suffix(".mp3")
        _edge(texto, mp3, voz)
        fuente = mp3
    elif motor == "espeak":
        fuente = destino.with_suffix(".raw.wav")
        _espeak(texto, fuente)
    else:
        raise ValueError(f"Motor de voz desconocido: {motor}")
    # Normalizamos todo a WAV estéreo 44.1 kHz con un respiro de 0,3 s al final.
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(fuente), "-af", "apad=pad_dur=0.3",
         "-ar", "44100", "-ac", "2", "-c:a", "pcm_s16le", str(wav)],
        check=True,
    )
    return wav
