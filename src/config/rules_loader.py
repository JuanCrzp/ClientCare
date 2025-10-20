from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
RULES_FILE = ROOT / "config" / "rules.yaml"

_cache = None

def get_rules():
    global _cache
    if _cache is None:
        _cache = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or {}
    return _cache

def get_rules_for(chat_id: str | None):
    rules = get_rules()
    if chat_id and chat_id in rules:
        base = rules.get("default", {}) or {}
        override = rules.get(chat_id) or {}
        # merge simple (override sobre default)
        merged = {**base, **override}
        return merged
    return rules.get("default", {}) or {}

def reload_rules_cache():
    global _cache
    _cache = None
