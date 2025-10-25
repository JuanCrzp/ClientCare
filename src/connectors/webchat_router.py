from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from ..bot_core.manager import BotManager
import os

router = APIRouter(prefix="/webchat", tags=["webchat"])
manager = BotManager()
SHARED = os.getenv("WEBCHAT_SHARED_SECRET", "").strip()


class WebchatMessage(BaseModel):
    user_id: str
    text: str
    chat_id: str | None = None


def _auth(x_api_key: str | None = Header(default=None)):
    if SHARED and (x_api_key or "") != SHARED:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/message")
def post_message(msg: WebchatMessage, _=Depends(_auth)):
    payload = {
        "platform": "webchat",
        "platform_user_id": msg.user_id,
        "group_id": msg.chat_id or "",
        "text": msg.text,
    }
    res = manager.process_message(payload) or {}
    # Si manager devuelve mensajes múltiples, devolvemos esa estructura para que el cliente la respete
    if res.get("messages"):
        return {"ok": True, "response": {"messages": res.get("messages")}}
    return {"ok": True, "response": res}
