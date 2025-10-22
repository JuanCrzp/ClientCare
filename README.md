<p align="center">
   <img src="docs/clientcare_banner.svg" alt="ClientCare Bot Banner" width="700"/>
</p>



<p align="center">
   <!-- Reemplaza ORG/REPO por tu organización y repo en GitHub para activar el badge -->
   <a href=".github/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/ORG/REPO/ci.yml?style=flat-square" alt="CI" /></a>
   <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square" alt="License" /></a>
   <a href="docs/architecture.md"><img src="https://img.shields.io/badge/Arquitectura-Doc-lightgrey?style=flat-square" alt="Arquitectura" /></a>
   <a href="docs/deployment.md"><img src="https://img.shields.io/badge/Despliegue-Guía-informational?style=flat-square" alt="Despliegue" /></a>
   <a href="docs/estructura.md"><img src="https://img.shields.io/badge/Estructura-Carpetas-success?style=flat-square" alt="Estructura" /></a>
</p>

> Bot profesional de atención al cliente, multicanal, 100% configurable via `config/rules.yaml`, con NLU avanzado y extensible, menús dinámicos y pruebas automatizadas. Listo para empresas SaaS.

---

## 📑 Tabla de Contenidos

- [Descripción General](#-descripción-general)
- [Arquitectura](#-arquitectura)
- [Flujo de Uso Típico](#-flujo-de-uso-típico)
- [Inicio Rápido](#-inicio-rápido)
- [Conectores Multicanal](#-conectores-multicanal)
- [Configuración](#-configuración)
- [Contrato de Mensajes (API)](#-contrato-de-mensajes-api)
- [Ejemplos y Pruebas](#-ejemplos-y-pruebas)
- [Estructura de Carpetas](#-estructura-de-carpetas)
- [Buenas Prácticas y Despliegue](#-buenas-prácticas-y-despliegue)
- [Checklist de Validación (QA)](#-checklist-de-validación-qa)
- [Comandos Rápidos](#-comandos-rápidos)
- [Roadmap y Extensibilidad](#-roadmap-y-extensibilidad)
- [Créditos y Licencia](#-créditos-y-licencia)

---

## 🚀 Descripción General

ClientCare es un bot modular para atención al cliente, diseñado para empresas SaaS que buscan automatizar FAQ, gestión de tickets, escalamiento a agentes y soporte multicanal (Telegram, Webchat, WhatsApp Cloud API). Toda

ClientCare es un bot modular para atención al cliente, diseñado para empresas SaaS que buscan automatizar FAQ, gestión de tickets, escalamiento a agentes y soporte multicanal (Telegram, Webchat, WhatsApp Cloud API). Toda la lógica y flujos se configuran en `config/rules.yaml` y `.env`, sin tocar el código.

---

## 🧠 NLU con Machine Learning (sin servicios externos)

---

## 🧠 Memoria Conversacional y Gestión de Contexto (NUEVO)

Desde octubre 2025, ClientCare incorpora un sistema profesional de memoria conversacional y gestión de contexto, listo para empresas y migración a base de datos.

### Características principales:
- **Historial persistente** por usuario/chat (límite configurable, por defecto 100 mensajes)
- **Temas abiertos** con TTL (días), para retomar conversaciones pendientes
- **Oferta automática de reanudar** si el usuario vuelve tras X minutos (configurable)
- **Comando `/historial`**: muestra los últimos mensajes del usuario (con privacidad opcional)
- **Comando `/continuar`**: retoma el tema pendiente si existe
- **Comandos admin**: `/admin reset_greeting <user_id>`, `/admin clear_history <user_id>`, `/admin set_topic <user_id> <topic>`
- **Configuración centralizada** en `config/rules.yaml`:

```yaml
memory:
   enabled: true
   history_max: 100
   resume_after_minutes: 60
   topic_ttl_days: 14
   offer_resume_message: "Veo que tenías pendiente: {topic}. ¿Quieres continuar?"
   history_command_enabled: true
   history_privacy_mask_emails: true
```

### Ejemplo de uso
- Usuario inicia conversación, el bot registra cada mensaje y detecta si hay temas pendientes.
- Si el usuario vuelve tras un tiempo, el bot le ofrece continuar donde lo dejó.
- El usuario puede consultar su historial con `/historial`.
- Los administradores pueden gestionar saludos, historial y temas vía `/admin`.

### Migración a MySQL
- El repositorio de conversaciones (`src/storage/conversation_repository.py`) está diseñado para migrar fácilmente a MySQL u otra base de datos relacional.
- Solo es necesario reemplazar la lógica de lectura/escritura JSON por queries SQL.
- Estructura sugerida: tabla `conversations` (user_id, chat_id, history, topic, last_active, expires_at).

---

El bot incluye un clasificador NLU propio basado en Naive Bayes Multinomial con n-gramas (caracteres y palabras). Se entrena directamente desde `rules.nlu.intents.patterns` y se serializa en `data/models/nlu_nb.pkl`.

Características clave:
- Entrenamiento 100% local (sin APIs externas)
- N-gramas de caracteres (3–5) y palabras (1–2) configurables
- Suavizado de Laplace (`alpha`) y umbral (`threshold`) ajustables
- Persistencia en disco y reporte de metadatos del modelo

Activación en `config/rules.yaml` (`default.nlu`):

```yaml
provider: ml
ml:
   retrain_on_start: false     # true para reentrenar en cada arranque (desarrollo)
   model_path: data/models/nlu_nb.pkl
   char_ngrams: [3, 5]
   word_ngrams: [1, 2]
   alpha: 1.0
threshold: 0.78
```

Entrenamiento y verificación:

```cmd
# Entrenar desde rules (genera nlu_nb.pkl y nlu_report.json)
.venv\Scripts\python.exe scripts\train_nlu.py

# Ver estado del modelo (ruta, labels, vocab_size, checksum, fechas, etc.)
.venv\Scripts\python.exe scripts\nlu_info.py
```

Reporte generado: `data/models/nlu_report.json` con metadatos del modelo (timestamp, número de ejemplos, distribución por label, tamaño de vocabulario, n-gramas, alpha, threshold y checksum de intents).

Si `provider` no se define o es `simple`, se usa el clasificador difuso por defecto (totalmente compatible).


## 🏗️ Arquitectura

```
Telegram/Webchat/WhatsApp
            │
   [Connectors]
            │
   [BotManager]
            │
    [Handlers]
            │
    [Storage]
```

- **Conectores**: Telegram (polling), Webchat (API HTTP), WhatsApp (Cloud API)
- **Orquestador**: BotManager centraliza flujos y reglas
- **Handlers**: greeting, FAQ, ticket, escalamiento, fallback
- **Persistencia**: Tickets en JSON (migrable a DB)
- **Configuración**: Todo en `config/rules.yaml` y `.env`

Más detalles: [`docs/architecture.md`](docs/architecture.md)

---

## 🔄 Flujo de Uso Típico

1. Usuario inicia conversación (Telegram/Webchat/WhatsApp)
2. El bot saluda y/o muestra menú (FAQ, ticket, agente)
3. Usuario pregunta → FAQ responde automáticamente
4. Usuario crea ticket → se guarda y devuelve ID
5. Usuario pide agente → bot solicita datos y deriva
6. Usuario consulta estado de ticket
7. Cierre o derivación a CRM/soporte humano

---

## ⚡ Inicio Rápido

### Windows
1. Copia `.env.example` a `.env` y configura tus tokens (Telegram, Webchat, WhatsApp)
2. Instala dependencias:
    ```cmd
    pip install -r requirements.txt
    ```
3. Ejecuta:
    ```cmd
    lanzar_bot.bat
    ```
    (Abre dos ventanas: Telegram y API HTTP)

### Linux/Mac
1. Configura `.env` y dependencias como arriba
2. Ejecuta en dos terminales:
    ```bash
    python -m src.connectors.telegram_polling
    uvicorn src.app.server:app --host 0.0.0.0 --port 8082 --reload
    ```

### Docker (experimental)
```bash
docker build -t atencion-cliente .
docker run -e TELEGRAM_TOKEN=XXX atencion-cliente
```

---

## 🔌 Conectores Multicanal

### Telegram
- Usa `python-telegram-bot` v20+ en modo polling
- Comandos: `/start`, `/help`, `/ticket <id>`, `/reload`
- Prueba: busca tu bot en Telegram y escribe `/start` o "precios"

### Webchat (API HTTP)
- Endpoint: `POST /webchat/message`
- Header: `x-api-key: <WEBCHAT_SHARED_SECRET>`
- Body ejemplo:
   ```json
   {"user_id": "123", "text": "precios", "chat_id": "opcional"}
   ```
 - Responde con JSON `{ok: true, response: {...}}`
 - Guía: [`docs/webchat_api.md`](docs/webchat_api.md)

### WhatsApp Cloud API
- Webhook: `GET/POST /whatsapp/webhook`
- Configura tokens en `.env`
 - Recibe mensajes y responde usando la Graph API de Meta
 - Guía: [`docs/whatsapp_setup.md`](docs/whatsapp_setup.md)

---

## ⚙️ Configuración

### Variables de entorno (`.env`)
Ver `.env.example`:
```
TELEGRAM_TOKEN=xxx
TELEGRAM_BOT_NAME=AtencionClienteBot
ADMIN_IDS=12345,67890
WEBCHAT_SHARED_SECRET=clavewebchat
WHATSAPP_VERIFY_TOKEN=tokenmeta
WHATSAPP_ACCESS_TOKEN=tokenapi
WHATSAPP_PHONE_NUMBER_ID=123456
DATA_DIR=data
```

### Reglas y flujos (`config/rules.yaml`)
Todo el comportamiento se define aquí, con comentarios en español. Ejemplo:
```yaml
default:
   enabled: true
   greetings_enabled: true
   menu_text: "Elige una opción: 1) FAQ 2) Ticket 3) Agente"
   features:
      faq: {enabled: true}
      tickets: {enabled: true}
      escalation: {enabled: true}
   synonyms:
      menu: ["menu", "hola", "buenas"]
      ticket: ["ticket", "soporte"]
      agent: ["agente", "humano"]
   faq:
      - q: "precios"
         a: "Nuestros planes comienzan en $X/mes."
   escalation:
      message: "Voy a derivarte con un agente."
   tickets:
      message_opened: "He creado tu ticket #{ticket_id}."
   rate_limit:
      per_user_per_minute: 30
```
Ver archivo completo: [`config/rules.yaml`](config/rules.yaml)

Más detalles en la referencia de reglas: [`docs/rules_reference.md`](docs/rules_reference.md)

---

## 🧪 Ejemplos y Pruebas

### Telegram
- `/start`, "precios", "ticket", "/ticket 1", "agente"

### Webchat (cURL)
```bash
curl -X POST http://localhost:8082/webchat/message \
   -H "x-api-key: <WEBCHAT_SHARED_SECRET>" \
   -H "Content-Type: application/json" \
   -d '{"user_id": "123", "text": "precios"}'
```

### WhatsApp
- Configura webhook en Meta y prueba enviando mensajes al número configurado

---

## � Contrato de Mensajes (API)

Entrada esperada por el core:
```json
{
   "platform": "telegram|webchat|whatsapp",
   "platform_user_id": "12345",
   "group_id": "-100999",
   "text": "Hola, quiero ayuda",
   "attachments": [],
   "raw_payload": {}
}
```

Salida típica del core:
```json
{
   "text": "¡Bienvenido! ¿En qué puedo ayudarte?",
   "type": "reply|ticket|escalation|faq",
   "quick_replies": ["Ver FAQ", "Crear ticket"],
   "attachments": []
}
```

---

## �📁 Estructura de Carpetas

```
ClientCare/
   README.md
   pyproject.toml
   requirements.txt
   .env.example
   lanzar_bot.bat
   src/
      app/
      bot_core/
      handlers/
      connectors/
      nlu/
      storage/
      tasks/
      utils/
   config/
      rules.yaml
   docs/
      architecture.md
      deployment.md
      windows_guide.md
   infra/
      docker/
         Dockerfile
   tests/
   examples/
```

---

## 🛠️ Buenas Prácticas y Despliegue

- Separa lógica de FAQ, tickets y escalamiento en handlers.
- Versiona `config/rules.yaml` y usa overrides por canal/cliente.
- Añade logs y métricas por canal.
- Asegura `.env` y haz backup de `data/`.
- Para 24/7: usa VPS/Cloud/Docker y health checks.

---

## ✅ Checklist de Validación (QA)

1. `/start` muestra menú y `/health` responde ok.
2. FAQ responde a “precios”, “integración”, etc.
3. `ticket` crea ticket y devuelve ID.
4. `/ticket <id>` muestra estado.
5. “agente” activa el flujo de escalamiento.
6. Webchat devuelve `{ok:true}` y WhatsApp responde por Graph API.
7. Rate limit bloquea spam según `rules.yaml`.
8. `enabled: false` hace que el bot ignore mensajes.

---

## ⚡ Comandos Rápidos

### Windows
```bat
lanzar_bot.bat
```
### Linux/Mac
```bash
python -m src.connectors.telegram_polling
uvicorn src.app.server:app --host 0.0.0.0 --port 8082 --reload
```
### Docker
```bash
docker build -t atencion-cliente .
docker run -e TELEGRAM_TOKEN=XXX atencion-cliente
```

---

## 🛠️ Roadmap y Extensibilidad
- Persistencia avanzada: SQLite/Postgres
- Integración CRM/ERP
- UI de administración
- Más canales: Messenger, Email, etc.
- Flujos personalizados por cliente

---

## 👨‍💻 Créditos y Licencia

Desarrollado por Juan Camilo Cruz P (github: JuanCrzp).

Licencia Apache-2.0. Ver archivo `LICENSE`.

---

## 📚 Documentación Adicional
- [`docs/architecture.md`](docs/architecture.md): Arquitectura y diagramas
- [`docs/deployment.md`](docs/deployment.md): Guía de despliegue
- [`docs/windows_guide.md`](docs/windows_guide.md): Guía rápida Windows
- [`docs/rules_reference.md`](docs/rules_reference.md): Guía completa de reglas
- [`docs/whatsapp_setup.md`](docs/whatsapp_setup.md): Configuración WhatsApp Cloud API
- [`docs/webchat_api.md`](docs/webchat_api.md): API de Webchat y ejemplos
- [`docs/faq.md`](docs/faq.md): Troubleshooting / preguntas frecuentes
- [`config/rules.yaml`](config/rules.yaml): Todas las reglas y flujos

---

¿Dudas o sugerencias? Abre un issue o contacta al equipo.

---

Nota: Este repo usa GitHub Actions para CI (`.github/workflows/ci.yml`), hooks opcionales de `pre-commit` (`.pre-commit-config.yaml`) y Dependabot para mantener dependencias al día (`.github/dependabot.yml`).

## 🔐 Seguridad

Consulta `SECURITY.md` para conocer el proceso de reporte de vulnerabilidades y tiempos de respuesta. Nunca subas secretos ni archivos `.env`.

## 🤝 Contribuir

Lee `CONTRIBUTING.md` para el flujo de trabajo, cómo ejecutar pruebas y cómo usar los hooks de `pre-commit`.
