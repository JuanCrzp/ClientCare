
import logging
logging.basicConfig(level=logging.DEBUG)
from fastapi import APIRouter, Request, HTTPException
import os
import httpx
from ..bot_core.manager import BotManager
import asyncio

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])
manager = BotManager()

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "").strip()
# NOTE: read ACCESS_TOKEN and PHONE_ID at call-time to allow runtime updates if the process env is changed
_token_invalid_until = 0.0



@router.get("/webhook")
async def verify(req: Request):
    """Verificación del webhook (Meta)"""
    params = req.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    logging.info(f"Webhook verify request: mode={mode} token={token} challenge={challenge}")
    if mode == "subscribe" and token == VERIFY_TOKEN and challenge is not None:
        try:
            return int(challenge)
        except Exception:
            logging.exception("Invalid challenge in webhook verification")
            raise HTTPException(status_code=400, detail="Invalid challenge")
    logging.warning("Webhook verification failed: invalid token or mode")
    raise HTTPException(status_code=403, detail="Verification failed")


async def _send_whatsapp_text(to: str, text: str):
    """Enviar texto a WhatsApp Cloud API.

    Lee el token y phone_id en cada llamada para permitir cambios en tiempo de ejecución
    y evita repetir llamadas cuando el token devuelve 401 (se aplica un bloqueo temporal).
    """
    import time
    global _token_invalid_until

    # Releer variables de entorno por llamada (si se actualizan en el entorno del proceso)
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()

    if not (access_token and phone_id):
        logging.warning("WhatsApp tokens not configured - skipping actual send")
        return

    now = time.time()
    if now < _token_invalid_until:
        logging.warning(f"Skipping WhatsApp send because previous token error flagged token invalid until {time.ctime(_token_invalid_until)}")
        return

    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text[:4096]},
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            logging.info(f"Posting to WhatsApp API url={url} to={to} payload={payload}")
            resp = await client.post(url, headers=headers, json=payload)
            # Registrar status y cuerpo para depuración
            try:
                body = resp.text
            except Exception:
                body = '<non-text-body>'
            logging.info(f"WhatsApp API response: status={resp.status_code} body={body}")

            # Manejo explícito de 401: marcar token como inválido por un tiempo para evitar spam
            if resp.status_code == 401:
                # Bloquear nuevos intentos por 5 minutos
                _token_invalid_until = time.time() + 300
                logging.error(
                    "WhatsApp API returned 401 Unauthorized. The access token appears expired or invalid. "
                    "Please renew WHATSAPP_ACCESS_TOKEN in environment and restart the process (or update process env). "
                    "Further WhatsApp sends will be skipped for 5 minutes to avoid repeated 401s."
                )
        except Exception as e:
            logging.exception(f"Error sending message to WhatsApp API for {to}: {e}")


@router.post("/webhook")
async def receive(request: Request):
    # Proteger la lectura del JSON para evitar 500 si el body no es JSON válido
    try:
        data = await request.json()
    except Exception as e:
        logging.exception("Invalid JSON in webhook POST")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Log completo de la petición para depuración
    logging.info(f"Webhook POST received: {data}")

    # Extraer mensajes entrantes básicos
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []) or []:
                    from_id = msg.get("from")  # número de usuario
                    text = (msg.get("text", {}) or {}).get("body", "")
                    logging.info(f"Incoming message from {from_id}: {text}")
                    payload = {
                        "platform": "whatsapp",
                        "platform_user_id": from_id,
                        "group_id": value.get("metadata", {}).get("display_phone_number", ""),
                        "text": text,
                    }
                    res = manager.process_message(payload) or {}
                    logging.info(f"Manager response for {from_id}: {res}")
                    logging.debug(f"[DEBUG] Respuesta completa del manager (payload={payload}): {res}")
                    # Soportar respuestas múltiples con delays: {'messages': [{'text': 'a'}, {'text': 'b', 'delay':5}]}
                    if res.get("messages") and isinstance(res.get("messages"), list):
                        for m in res.get("messages"):
                            try:
                                d = float(m.get("delay", 0) or 0)
                            except Exception:
                                d = 0
                            if d > 0:
                                logging.info(f"Delaying {d}s before sending next message to {from_id}")
                                await asyncio.sleep(d)
                            text_to_send = str(m.get("text") or "")
                            if text_to_send:
                                logging.info(f"Sending reply to {from_id}: {text_to_send}")
                                await _send_whatsapp_text(from_id, text_to_send)
                    elif res.get("text"):
                        logging.info(f"Sending reply to {from_id}: {res['text']}")
                        await _send_whatsapp_text(from_id, res["text"])            
    except Exception as e:
        # Registrar excepción para poder depurar y devolver 500 para visibilidad
        logging.exception(f"Error processing webhook POST: {e}")
        raise HTTPException(status_code=500, detail="Error processing webhook event")

    return {"ok": True}
