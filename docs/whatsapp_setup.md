# Configuración de WhatsApp Cloud API

Esta guía explica cómo conectar el bot a WhatsApp Cloud API (Meta).

## Prerrequisitos
- Cuenta de Meta Developers y App creada
- Número de prueba o de negocio en WhatsApp Cloud API
- Verificación del negocio (opcional para producción)

## Variables `.env`
- `WHATSAPP_VERIFY_TOKEN`: token para verificación del webhook
- `WHATSAPP_ACCESS_TOKEN`: token de acceso de Graph API
- `WHATSAPP_PHONE_NUMBER_ID`: ID del número asociado

## Pasos
1. En Meta Developers, en Webhooks registra la URL de verificación:
   - `GET https://TU_HOST/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<WHATSAPP_VERIFY_TOKEN>&hub.challenge=123456`
   - El bot devolverá `123456` si el token es correcto.
2. Configura el webhook para eventos de `messages`.
3. Define las variables en `.env` y arranca la API:
   - `uvicorn src.app.server:app --host 0.0.0.0 --port 8082`
4. Prueba enviando un mensaje desde un número permitido.

## Notas
- El bot responde con texto simple (`_send_whatsapp_text`) usando Graph API.
- Para plantillas y medios, amplía el payload en `src/connectors/whatsapp_router.py`.
