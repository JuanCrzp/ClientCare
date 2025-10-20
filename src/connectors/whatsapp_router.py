from fastapi import APIRouter, Request, HTTPException
import os
import httpx
from ..bot_core.manager import BotManager

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
manager = BotManager()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()


@router.get("/webhook")
async def verify(req: Request):
    """Verificación del webhook (Meta)"""
    params = req.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge is not None:
        try:
            return int(challenge)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid challenge")
    raise HTTPException(status_code=403, detail="Verification failed")


async def _send_whatsapp_text(to: str, text: str):
    if not (ACCESS_TOKEN and PHONE_ID):
        return
    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(url, headers=headers, json=payload)


@router.post("/webhook")
async def receive(request: Request):
    data = await request.json()
    # Extraer mensajes entrantes básicos
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []) or []:
                    from_id = msg.get("from")  # número de usuario
                    text = (msg.get("text", {}) or {}).get("body", "")
                    payload = {
                        "platform": "whatsapp",
                        "platform_user_id": from_id,
                        "group_id": value.get("metadata", {}).get("display_phone_number", ""),
                        "text": text,
                    }
                    res = manager.process_message(payload) or {}
                    if res.get("text"):
                        await _send_whatsapp_text(from_id, res["text"])
    except Exception:
        # Silencioso para no romper el webhook, inspecciona logs si es necesario
        pass
    return {"ok": True}
