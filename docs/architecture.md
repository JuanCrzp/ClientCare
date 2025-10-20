# Arquitectura - AtencionCliente

- Conector Telegram (polling) -> BotManager -> Handlers -> Storage
- Configuración centralizada en `config/rules.yaml` con overrides por chat.
- API FastAPI para health y futura administración.
- Persistencia JSON de tickets (migrable a DB).
