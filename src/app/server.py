from fastapi import FastAPI
from .config import settings
from ..connectors.webchat_router import router as webchat_router
from ..connectors.whatsapp_router import router as whatsapp_router

app = FastAPI(title="AtencionCliente API")

@app.get("/health")
def health():
    return {"status": "ok", "bot": settings.telegram_bot_name}

# Montar conectores HTTP
app.include_router(webchat_router)
app.include_router(whatsapp_router)
