from ..config.rules_loader import get_rules

def answer_faq(text: str) -> str | None:
    rules = get_rules().get("default", {})
    faq = rules.get("faq", []) or []
    t = text.lower()
    for item in faq:
        q = (item.get("q") or "").lower()
        if q and q in t:
            return item.get("a") or None
    return None
