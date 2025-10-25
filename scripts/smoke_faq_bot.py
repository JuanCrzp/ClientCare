import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.bot_core.manager import BotManager  # noqa: E402

samples = [
    "horario",
    "¿a qué hora abren?",
    "dónde están ubicados",
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

bot = BotManager()
for s in samples:
    r = bot.process_message({"text": s, "platform_user_id": "smoke", "group_id": "g1"})
    print(f">> {s!r}\n{r}\n")
