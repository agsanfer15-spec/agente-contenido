"""Línea de comandos del agente de contenido."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .agente import idea_a_video, producir
from .guion import Guion
from .voz import VOZ_POR_DEFECTO


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="agente-contenido",
        description="Convierte una idea en un video corto vertical (720x1280) con guion de IA y montaje en ffmpeg.",
    )
    p.add_argument("idea", nargs="?", help="La idea del video, entre comillas.")
    p.add_argument("--guion", type=Path, help="Usar un guion JSON ya escrito (no llama a ninguna IA).")
    p.add_argument("--solo-guion", action="store_true", help="Solo escribir el guion e imprimirlo en JSON.")
    p.add_argument("--motor-guion", choices=["claude", "ollama"], default="claude",
                   help="Quién escribe el guion: Claude (API de pago) u Ollama (local y gratis).")
    p.add_argument("--modelo", help="Modelo a usar (por defecto claude-sonnet-5-5 o llama3.1).")
    p.add_argument("--duracion", type=int, default=60, help="Duración objetivo en segundos (por defecto 60).")
    p.add_argument("--tono", default="cercano y enérgico", help="Tono del guion.")
    p.add_argument("--voz", choices=["edge", "espeak", "ninguna"], default="edge", help="Motor de voz.")
    p.add_argument("--voz-nombre", default=VOZ_POR_DEFECTO, help="Voz de edge-tts (p. ej. es-ES-AlvaroNeural).")
    p.add_argument("--marca", default="", help="Texto de marca arriba del video, p. ej. @tucuenta.")
    p.add_argument("--fuente", help="Ruta a una fuente .ttf negrita.")
    p.add_argument("--salida", type=Path, default=Path("salida"), help="Carpeta de salida.")
    a = p.parse_args(argv)

    opciones = dict(motor_voz=a.voz, voz_nombre=a.voz_nombre, marca=a.marca, fuente=a.fuente)

    if a.guion:
        guion = Guion.desde_dict(json.loads(a.guion.read_text(encoding="utf-8")))
        print(f"Produciendo «{guion.titulo}» desde {a.guion}…")
        r = producir(guion, a.salida, **opciones)
    else:
        if not a.idea:
            p.error("Escribe una idea o usa --guion archivo.json")
        if a.motor_guion == "claude" and not os.environ.get("ANTHROPIC_API_KEY"):
            p.error("Falta ANTHROPIC_API_KEY (https://console.anthropic.com). "
                    "Alternativas gratis: --motor-guion ollama, o --guion archivo.json")
        if a.solo_guion:
            from .guion import generar_guion
            g = generar_guion(a.idea, a.duracion, a.tono, a.motor_guion, a.modelo)
            print(json.dumps(g.a_dict(), ensure_ascii=False, indent=2))
            return 0
        r = idea_a_video(a.idea, a.salida, a.duracion, a.tono, a.motor_guion, a.modelo, **opciones)

    print(f"\nListo: {r.video} ({r.duracion:.1f} s)")
    print(f"Guion: {r.guion_json}\nDescripción para publicar: {r.descripcion}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
