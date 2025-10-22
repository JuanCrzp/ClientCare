import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))

from src.bot_core.manager import BotManager

samples = [
    "abrirr tiket",
    "ver menu",
    "hablar con agente",
    "planes",
    "men",
]

bot = BotManager()
for s in samples:
    r = bot.process_message({"text": s, "platform_user_id": "smoke", "group_id": "g1"})
    print(f">> {s!r}\n{r}\n")
