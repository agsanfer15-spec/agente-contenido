import json
import shutil
import subprocess
from pathlib import Path

import pytest

from agente_contenido.agente import producir
from agente_contenido.guion import Guion, escenas_para, extraer_json

EJEMPLO = Path(__file__).parent.parent / "ejemplos" / "guion_ejemplo.json"


def test_extraer_json_tolera_bloque_de_codigo():
    texto = 'Aquí tienes:\n```json\n{"titulo": "x", "escenas": []}\n```'
    assert extraer_json(texto)["titulo"] == "x"


def test_guion_desde_dict_y_bloques():
    g = Guion.desde_dict(json.loads(EJEMPLO.read_text(encoding="utf-8")))
    bloques = g.bloques()
    assert len(bloques) == len(g.escenas) + 2  # gancho + escenas + cierre
    assert bloques[0].narracion == g.gancho


def test_guion_sin_escenas_falla():
    with pytest.raises(ValueError):
        Guion.desde_dict({"titulo": "x", "escenas": []})


def test_escenas_para_limites():
    assert escenas_para(10) == 3
    assert escenas_para(60) == 7
    assert escenas_para(300) == 8


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg no instalado")
def test_producir_video_vertical(tmp_path):
    g = Guion.desde_dict(json.loads(EJEMPLO.read_text(encoding="utf-8")))
    g.escenas = g.escenas[:1]  # rápido
    r = producir(g, tmp_path, motor_voz="ninguna", avisar=lambda *_: None)
    assert r.video.exists()
    info = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(r.video)],
        capture_output=True, text=True, check=True).stdout)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    assert (v["width"], v["height"]) == (720, 1280)
    assert any(s["codec_type"] == "audio" for s in info["streams"])
