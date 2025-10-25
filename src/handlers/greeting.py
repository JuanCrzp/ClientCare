from ..config.rules_loader import get_rules_for


def build_greeting(user: str, chat_id: str | None = None) -> str:
    rules = get_rules_for(chat_id)
    # Si greeting_enabled es false, no mostrar saludo
    if not rules.get("greeting_enabled", True):
        return ""

    # Config de menú para decidir si mencionarlo
    menus_cfg = dict(rules.get("menus") or {})
    menus_enabled = bool(menus_cfg.get("enabled", True)) and bool(menus_cfg.get("items") or {})
    gmp_enabled = bool(rules.get("greeting_menu_prompt_enabled", True))
    gmp_text = str(rules.get("greeting_menu_prompt_text") or "Si necesitas ver las opciones, dime 'menú' y te las envío.")

    # Usa greeting_text si está definido
    greeting = (rules.get("greeting_text") or "").replace("{user}", user or "").strip()
    if not greeting:
        greeting = (
            f"¡Hola {user}! Soy tu asistente virtual de atención al cliente.\n"
            "Estoy aquí para ayudarte: puedes consultar el FAQ, abrir un ticket o hablar con un agente."
        )

    # El saludo NO debe incluir el prompt del menú, solo el texto puro.

    return greeting
