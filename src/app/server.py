from fastapi import FastAPI, Request, HTTPException
from .config import settings
from ..connectors.webchat_router import router as webchat_router
from ..connectors.whatsapp_router import router as whatsapp_router
import os
from ..config.rules_loader import reload_rules_cache, get_rules

app = FastAPI(title="AtencionCliente API")

@app.get("/health")
def health():
    return {"status": "ok", "bot": settings.telegram_bot_name}

# Montar conectores HTTP
app.include_router(webchat_router)
app.include_router(whatsapp_router)


@app.get("/admin/reload_rules")
async def admin_reload(req: Request):
    """Recargar reglas en el proceso actual. Opcionalmente protege con ADMIN_RELOAD_TOKEN env var.

    - Si ADMIN_RELOAD_TOKEN está definido, se debe enviar en header X-Admin-Token o query ?token=...
    - Devuelve 200 y las claves principales de rules tras recargar, o 500 con error de parseo.
    """
    configured = os.getenv("ADMIN_RELOAD_TOKEN")
    token = req.headers.get("X-Admin-Token") or req.query_params.get("token")
    if configured and token != configured:
        raise HTTPException(status_code=403, detail="Forbidden: invalid token")
    try:
        reload_rules_cache()
        rules = get_rules()
        # devolver keys para verificación rápida
        return {"status": "ok", "top_keys": list(rules.keys())[:20]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
