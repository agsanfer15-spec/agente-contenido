"""Orquestador: idea → guion → voz → video."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from . import video, voz
from .guion import Guion, generar_guion


@dataclass
class Resultado:
    guion: Guion
    video: Path
    guion_json: Path
    descripcion: Path
    duracion: float


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:50] or "video"


def producir(guion: Guion, carpeta: Path, motor_voz: str = "edge", voz_nombre: str = voz.VOZ_POR_DEFECTO,
             marca: str = "", fuente: str | None = None, avisar=print) -> Resultado:
    """Convierte un guion ya escrito en video. Devuelve las rutas generadas."""
    carpeta.mkdir(parents=True, exist_ok=True)
    trabajo = carpeta / "_trabajo"
    trabajo.mkdir(exist_ok=True)
    fuente = fuente or video.fuente_disponible()
    nombre = _slug(guion.titulo)

    bloques = guion.bloques()
    clips, audios, total_seg = [], [], 0.0
    for i, bloque in enumerate(bloques):
        avisar(f"  · Bloque {i + 1}/{len(bloques)}: {bloque.texto_pantalla}")
        audio = voz.sintetizar(bloque.narracion, trabajo / f"voz_{i:02d}", motor_voz, voz_nombre)
        seg = voz.duracion_audio(audio)
        clip = video.render_clip(i, len(bloques), bloque.texto_pantalla, bloque.narracion, seg,
                                 trabajo / f"clip_{i:02d}.mp4", fuente, marca)
        clips.append(clip)
        audios.append(audio)
        total_seg += seg

    salida = video.unir(clips, audios, carpeta / f"{nombre}.mp4", trabajo)

    guion_json = carpeta / f"{nombre}.guion.json"
    guion_json.write_text(json.dumps(guion.a_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    descripcion = carpeta / f"{nombre}.descripcion.txt"
    descripcion.write_text(f"{guion.titulo}\n\n{guion.gancho}\n\n{guion.cierre}\n\n{' '.join(guion.hashtags)}\n",
                           encoding="utf-8")
    return Resultado(guion, salida, guion_json, descripcion, total_seg)


def idea_a_video(idea: str, carpeta: Path, duracion: int = 60, tono: str = "cercano y enérgico",
                 motor_guion: str = "claude", modelo: str | None = None, **opciones) -> Resultado:
    """Flujo completo: escribe el guion con IA y produce el video."""
    avisar = opciones.get("avisar", print)
    avisar(f"1/2 Escribiendo guion con {motor_guion}…")
    guion = generar_guion(idea, duracion, tono, motor_guion, modelo)
    avisar(f"    «{guion.titulo}» ({len(guion.escenas)} escenas)")
    avisar("2/2 Grabando voz y montando video…")
    return producir(guion, carpeta, **opciones)
