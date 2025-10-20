# Referencia de Reglas (rules.yaml)

Todas las configuraciones funcionales del bot viven en `config/rules.yaml`. Tokens/secretos van en `.env`.

## Estructura principal
- `default`: bloque base que aplica a todos los canales/chats.
- `"<chat_id>"`: claves opcionales que sobreescriben `default` para un canal/grupo específico.

## Claves y significado

### enabled
Activa/desactiva el bot para el chat.

### bot_name, locale, greetings_enabled, fallback_text
Metadatos y textos base del bot.

### menu_text
Texto del menú principal.

### features
- `connectors.telegram_enabled|webchat_enabled|whatsapp_enabled`: habilita conectores (requiere `.env`).
- `faq.enabled`, `faq.not_found_message`: control del FAQ.
- `tickets.enabled`, `tickets.category_options`, `tickets.default_priority`.
- `escalation.enabled`, `escalation.request_contact_fields`.

### synonyms
Palabras clave que detonan menú/ticket/agente.

### faq
Lista de Q/A simples (keywords). Para NLU avanzada, añade un motor NLU.

### escalation / tickets
Mensajes y plantillas para cada flujo.

### rate_limit
Límites anti-spam por usuario y global.

### admin_notify
Aviso a un canal/ID de admins al crear tickets.

## Overrides por chat
Ejemplo:
```yaml
default:
  features:
    faq: {enabled: true}
"-100123456789":
  features:
    faq: {enabled: false}
```
Sólo define lo que cambias; heredas del bloque `default`.
