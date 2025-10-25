import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.handlers.faq import answer_faq

samples = [
    "horario",
    "¿a qué hora abren?",
    "dónde están ubicados",
    "ubicación",
    "precios",
    "¿cuánto cuesta?",
    "envíos",
    "formas de pago",
    "devoluciones",
    "novedades",
    "contacto",
    "quiénes son",
    "redes sociales",
]

for s in samples:
    ans = answer_faq(s)
    print(f">> {s!r} -> {ans!r}")
