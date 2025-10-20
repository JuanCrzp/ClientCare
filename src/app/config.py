from pydantic import BaseModel
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

class Settings(BaseModel):
    telegram_token: str = os.getenv("TELEGRAM_TOKEN", "")
    telegram_bot_name: str = os.getenv("TELEGRAM_BOT_NAME", "AtencionClienteBot")
    data_dir: str = os.getenv("DATA_DIR", "data")

settings = Settings()
