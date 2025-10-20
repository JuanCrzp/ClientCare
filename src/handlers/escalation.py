from ..config.rules_loader import get_rules

def escalation_message() -> str:
    rules = get_rules().get("default", {})
    return rules.get("escalation", {}).get("message", "Te voy a derivar con un agente.")
