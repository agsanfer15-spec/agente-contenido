"""Paso 3: montar el video vertical con ffmpeg.

Cada bloque del guion se convierte en un clip con fondo degradado animado,
texto grande centrado y una barra de progreso; después se concatenan y se
añade el audio de la narración.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

ANCHO, ALTO, FPS = 720, 1280, 30

PALETAS = [
    ("0x1E3A8A", "0x7C3AED"),
    ("0x0F766E", "0x22C55E"),
    ("0xB91C1C", "0xF97316"),
    ("0x111827", "0x2563EB"),
    ("0x831843", "0xEC4899"),
    ("0x713F12", "0xEAB308"),
]

FUENTES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def fuente_disponible() -> str:
    for ruta in FUENTES:
        if Path(ruta).exists():
            return ruta
    raise RuntimeError("No encontré una fuente negrita. Pasa --fuente /ruta/a/fuente.ttf")


def _escapar(texto: str) -> str:
    """Escapa texto para el filtro drawtext de ffmpeg."""
    for a, b in (("\\", "\\\\\\\\"), (":", "\\:"), ("'", "\u2019"), ("%", "\\%"), (",", "\\,")):
        texto = texto.replace(a, b)
    return texto


def _ruta_fuente(ruta: str) -> str:
    """En Windows, ffmpeg necesita barras normales y ':' escapado en la ruta de la fuente."""
    return ruta.replace("\\", "/").replace(":", "\\:")


def _lineas(texto: str, ancho: int) -> list[str]:
    return textwrap.wrap(texto, width=ancho) or [" "]


def _capa_texto(lineas: list[str], fuente: str, tam: int, y_centro: int, color: str,
                caja: bool) -> list[str]:
    filtros = []
    alto_linea = int(tam * 1.25)
    y0 = y_centro - alto_linea * len(lineas) // 2
    for i, linea in enumerate(lineas):
        extra = ":box=1:boxcolor=black@0.35:boxborderw=18" if caja else ""
        filtros.append(
            f"drawtext=fontfile='{_ruta_fuente(fuente)}':text='{_escapar(linea)}':fontsize={tam}:fontcolor={color}"
            f":x=(w-text_w)/2:y={y0 + i * alto_linea}:borderw=3:bordercolor=black@0.6{extra}"
        )
    return filtros


def render_clip(indice: int, total: int, texto_pantalla: str, narracion: str, segundos: float,
                destino: Path, fuente: str, marca: str = "") -> Path:
    """Renderiza un clip mudo de `segundos` para un bloque del guion."""
    c1, c2 = PALETAS[indice % len(PALETAS)]
    filtros = [f"format=yuv420p"]
    filtros += _capa_texto(_lineas(texto_pantalla.upper(), 16), fuente, 64, ALTO // 2 - 140, "white", False)
    filtros += _capa_texto(_lineas(narracion, 30), fuente, 34, ALTO // 2 + 230, "white", True)
    # Barra de progreso global (de este clip dentro del video completo).
    inicio, fin = indice / total, (indice + 1) / total
    filtros.append(
        f"drawbox=x=0:y={ALTO - 24}:w='{ANCHO}*({inicio}+({fin}-{inicio})*t/{segundos:.3f})':h=24"
        f":color=white@0.85:t=fill"
    )
    if marca:
        filtros.append(
            f"drawtext=fontfile='{_ruta_fuente(fuente)}':text='{_escapar(marca)}':fontsize=28:fontcolor=white@0.8"
            f":x=(w-text_w)/2:y=70"
        )
    fondo = (f"gradients=s={ANCHO}x{ALTO}:c0={c1}:c1={c2}:x0=0:y0=0:x1={ANCHO}:y1={ALTO}"
             f":speed=0.02:rate={FPS}:d={segundos:.3f}")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", fondo,
         "-vf", ",".join(filtros), "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
         "-pix_fmt", "yuv420p", "-r", str(FPS), str(destino)],
        check=True,
    )
    return destino


def unir(clips: list[Path], audios: list[Path], salida: Path, trabajo: Path) -> Path:
    """Concatena clips y audios y los combina en el MP4 final."""
    lista_v = trabajo / "clips.txt"
    lista_a = trabajo / "audios.txt"
    lista_v.write_text("".join(f"file '{c.resolve().as_posix()}'\n" for c in clips), encoding="utf-8")
    lista_a.write_text("".join(f"file '{a.resolve().as_posix()}'\n" for a in audios), encoding="utf-8")
    audio = trabajo / "narracion.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                    "-i", str(lista_a), "-c", "copy", str(audio)], check=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista_v),
         "-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
         "-shortest", "-movflags", "+faststart", str(salida)],
        check=True,
    )
    return salida
