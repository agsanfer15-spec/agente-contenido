"""Paso 1: convertir una idea en un guion estructurado para video corto vertical."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field

MODELO_POR_DEFECTO = os.environ.get("AGENTE_MODELO", "claude-sonnet-5-5")

PROMPT_SISTEMA = """Eres un guionista experto en videos cortos verticales (TikTok, Reels, Shorts).
Escribes en español neutro, con frases cortas que se leen bien en pantalla y suenan naturales en voz alta.
Estructura obligatoria: un gancho fuerte en los primeros 3 segundos, desarrollo en escenas breves y un cierre con llamada a la acción.
Responde SOLO con JSON válido, sin texto antes ni después, con esta forma exacta:
{
  "titulo": "string (máx. 60 caracteres)",
  "gancho": "string (una frase que detenga el scroll)",
  "escenas": [
    {"narracion": "lo que dice la voz (1-2 frases)", "texto_pantalla": "texto corto en pantalla (máx. 6 palabras)", "visual": "descripción breve de la imagen o b-roll sugerido"}
  ],
  "cierre": "llamada a la acción final",
  "hashtags": ["#ejemplo"]
}"""


@dataclass
class Escena:
    narracion: str
    texto_pantalla: str
    visual: str = ""


@dataclass
class Guion:
    titulo: str
    gancho: str
    escenas: list[Escena]
    cierre: str
    hashtags: list[str] = field(default_factory=list)

    def bloques(self) -> list[Escena]:
        """Gancho + escenas + cierre como una sola lista de bloques para el montaje."""
        gancho = Escena(self.gancho, _recortar(self.gancho, 6), "gancho")
        cierre = Escena(self.cierre, _recortar(self.cierre, 6), "cierre")
        return [gancho, *self.escenas, cierre]

    def a_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def desde_dict(cls, datos: dict) -> "Guion":
        escenas = [Escena(**{k: e.get(k, "") for k in ("narracion", "texto_pantalla", "visual")})
                   for e in datos.get("escenas", [])]
        if not escenas:
            raise ValueError("El guion no tiene escenas.")
        return cls(
            titulo=datos.get("titulo", "Sin título"),
            gancho=datos.get("gancho", escenas[0].narracion),
            escenas=escenas,
            cierre=datos.get("cierre", ""),
            hashtags=list(datos.get("hashtags", [])),
        )


def _recortar(texto: str, max_palabras: int) -> str:
    palabras = texto.split()
    return " ".join(palabras[:max_palabras]) + ("…" if len(palabras) > max_palabras else "")


def extraer_json(texto: str) -> dict:
    """Saca el primer objeto JSON de la respuesta del modelo (tolera ```json ... ```)."""
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto.strip())
    inicio, fin = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fin == -1:
        raise ValueError("La respuesta del modelo no contiene JSON.")
    return json.loads(texto[inicio : fin + 1])


def escenas_para(duracion: int) -> int:
    """Unas 8-10 s por escena, entre 3 y 8 escenas."""
    return max(3, min(8, round(duracion / 9)))


def _pedido(idea: str, duracion: int, tono: str) -> str:
    return (
        f"Idea del video: {idea}\n"
        f"Duración objetivo: {duracion} segundos (unas {int(duracion * 2.4)} palabras de narración en total).\n"
        f"Número de escenas: {escenas_para(duracion)}.\n"
        f"Tono: {tono}."
    )


def _con_claude(pedido: str, modelo: str) -> str:
    import anthropic  # import perezoso: el modo --guion no necesita la API

    cliente = anthropic.Anthropic()
    respuesta = cliente.messages.create(
        model=modelo,
        max_tokens=2000,
        system=PROMPT_SISTEMA,
        messages=[{"role": "user", "content": pedido}],
    )
    return "".join(b.text for b in respuesta.content if getattr(b, "type", "") == "text")


def _con_ollama(pedido: str, modelo: str) -> str:
    """Modelo local y gratuito vía Ollama (https://ollama.com)."""
    import urllib.request

    url = os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/") + "/api/chat"
    cuerpo = json.dumps({
        "model": modelo, "stream": False, "format": "json",
        "messages": [{"role": "system", "content": PROMPT_SISTEMA}, {"role": "user", "content": pedido}],
    }).encode()
    peticion = urllib.request.Request(url, cuerpo, {"Content-Type": "application/json"})
    with urllib.request.urlopen(peticion, timeout=600) as r:
        return json.loads(r.read())["message"]["content"]


def generar_guion(idea: str, duracion: int = 60, tono: str = "cercano y enérgico",
                  motor: str = "claude", modelo: str | None = None) -> Guion:
    """Escribe el guion con Claude (necesita ANTHROPIC_API_KEY) u Ollama (local, gratis)."""
    pedido = _pedido(idea, duracion, tono)
    if motor == "claude":
        texto = _con_claude(pedido, modelo or MODELO_POR_DEFECTO)
    elif motor == "ollama":
        texto = _con_ollama(pedido, modelo or os.environ.get("OLLAMA_MODELO", "llama3.1"))
    else:
        raise ValueError(f"Motor de guion desconocido: {motor}")
    return Guion.desde_dict(extraer_json(texto))
