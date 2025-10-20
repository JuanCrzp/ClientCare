# FAQ / Troubleshooting

## No responde en Telegram
- Verifica `TELEGRAM_TOKEN` en `.env`.
- ¿Creaste el bot con @BotFather y activaste el token correcto?
- Revisa la consola del proceso `telegram_polling` por errores.

## 401 en Webchat
- El header `x-api-key` no coincide con `WEBCHAT_SHARED_SECRET`.

## Verificación WhatsApp falla
- El `hub.verify_token` no coincide con `WHATSAPP_VERIFY_TOKEN`.
- Asegúrate de que el servidor expone `GET /whatsapp/webhook` en HTTPS público.

## No crea tickets
- Verifica permisos de escritura en `DATA_DIR` (por defecto `data/`).
- Revisa logs de `src/storage/repository.py` si existen.

## Rate limit bloquea mensajes válidos
- Ajusta `rate_limit.per_user_per_minute` en `config/rules.yaml`.
