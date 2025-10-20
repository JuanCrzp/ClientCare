from ..config.rules_loader import get_rules_for

def build_greeting(user: str, chat_id: str | None = None) -> str:
    rules = get_rules_for(chat_id)
    # Si greeting_enabled es false, no mostrar saludo
    if not rules.get("greeting_enabled", True):
        return ""
    # Usa greeting_text si está definido, si no, usa uno por defecto
    greeting = rules.get("greeting_text")
    if greeting:
        return greeting.replace("{user}", user or "").strip()
    # Fallback clásico
    menu = rules.get("menu_text") or (
        "Elige una opción:\n1) FAQ\n2) Crear ticket\n3) Hablar con agente"
    )
    return f"¡Hola {user}! Soy tu asistente de atención.\n{menu}"
