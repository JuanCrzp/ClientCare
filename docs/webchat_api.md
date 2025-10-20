# API Webchat

Endpoint para integrar un widget o frontend web con el bot.

## Endpoint
- `POST /webchat/message`

## Autenticación
- Header: `x-api-key: <WEBCHAT_SHARED_SECRET>`

## Request
```json
{
  "user_id": "123",
  "text": "precios",
  "chat_id": "opcional"
}
```

## Response
```json
{
  "ok": true,
  "response": { "text": "Nuestros planes comienzan en $X/mes." }
}
```

## Ejemplos cURL
```bash
curl -X POST http://localhost:8082/webchat/message \
  -H "x-api-key: <WEBCHAT_SHARED_SECRET>" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","text":"precios"}'
```

## Errores comunes
- 401 Invalid API key → revisa `WEBCHAT_SHARED_SECRET`
- 422 Unprocessable Entity → verifica el JSON del body
