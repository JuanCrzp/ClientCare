# Estructura de Carpetas de ClientCare

Se actualiza automáticamente vía pre-commit. No editar manualmente.

```
(clientcare)
├── .github
│   ├── workflows
│   │   └── ci.yml
│   └── dependabot.yml
├── .vscode
│   └── settings.json
├── ci
│   └── pipeline.yml
├── config
│   └── rules.yaml
├── data
│   ├── models
│   │   ├── nlu_nb.pkl
│   │   └── nlu_report.json
│   ├── conversations.json
│   ├── state.json
│   └── tickets.json
├── docs
│   ├── sql
│   │   ├── erd.mmd
│   │   ├── README.md
│   │   └── schema.sql
│   ├── architecture.md
│   ├── clientcare_banner.svg
│   ├── deployment.md
│   ├── estructura.md
│   ├── faq.md
│   ├── faq_config.md
│   ├── rules_reference.md
│   ├── webchat_api.md
│   ├── whatsapp_ngrok_setup.md
│   ├── whatsapp_setup.md
│   └── windows_guide.md
├── examples
│   ├── sample_env_vars.md
│   └── sample_messages.json
├── infra
│   └── docker
│       └── Dockerfile
├── scripts
│   ├── debug_whatsapp_flow.py
│   ├── generate_tree.py
│   ├── nlu_info.py
│   ├── simulate_whatsapp_connector.py
│   ├── smoke_faq_bot.py
│   ├── smoke_nlu.py
│   ├── test_faq_match.py
│   └── train_nlu.py
├── src
│   ├── app
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── server.py
│   ├── atencion_cliente_bot.egg-info
│   │   ├── dependency_links.txt
│   │   ├── PKG-INFO
│   │   ├── requires.txt
│   │   ├── SOURCES.txt
│   │   └── top_level.txt
│   ├── bot_core
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── config
│   │   └── rules_loader.py
│   ├── connectors
│   │   ├── __init__.py
│   │   ├── telegram_polling.py
│   │   ├── webchat_router.py
│   │   └── whatsapp_router.py
│   ├── handlers
│   │   ├── __init__.py
│   │   ├── escalation.py
│   │   ├── faq.py
│   │   ├── greeting.py
│   │   └── ticket.py
│   ├── nlu
│   │   ├── __init__.py
│   │   └── classifier.py
│   ├── storage
│   │   ├── __init__.py
│   │   ├── conversation_repository.py
│   │   ├── repository.py
│   │   └── state_repository.py
│   ├── tasks
│   │   └── __init__.py
│   ├── utils
│   │   ├── __init__.py
│   │   ├── duration.py
│   │   └── rate_limiter.py
│   └── __init__.py
├── tests
│   ├── integration
│   ├── unit
│   │   ├── test_bot_capabilities.py
│   │   ├── test_conversation_repository.py
│   │   ├── test_duration_parser.py
│   │   ├── test_generate_tree.py
│   │   ├── test_inactivity_flow.py
│   │   ├── test_manager.py
│   │   ├── test_memory_resume.py
│   │   ├── test_nlu_advanced.py
│   │   └── test_repository.py
│   └── conftest.py
├── .coveragerc
├── .dockerignore
├── .env
├── .env.example
├── .gitattributes
├── .gitignore
├── .pre-commit-config.yaml
├── CONTRIBUTING.md
├── coverage.xml
├── DESCRIPCION_BOT
├── lanzar_bot.bat
├── LICENSE
├── payload.json
├── pyproject.toml
├── pytest.ini
├── README.md
├── requirements-dev.txt
├── requirements.txt
├── run.py
└── SECURITY.md
```
