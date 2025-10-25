from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
RULES_FILE = ROOT / "config" / "rules.yaml"

_cache = None
_cache_mtime = None


def _flatten(d, parent_key="", sep="."):
    items = {}
    for k, v in (d or {}).items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(_flatten(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items


def _interpolate_strings(obj, mapping):
    # Recursively replace {key} in strings using mapping (flat keys like 'catalog.link')
    import re

    pattern = re.compile(r"\{([^}]+)\}")

    if isinstance(obj, str):
        def repl(m):
            key = m.group(1)
            return str(mapping.get(key, m.group(0)))
        return pattern.sub(repl, obj)
    if isinstance(obj, dict):
        return {k: _interpolate_strings(v, mapping) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_interpolate_strings(v, mapping) for v in obj]
    return obj

def get_rules():
    global _cache
    global _cache_mtime
    try:
        mtime = RULES_FILE.stat().st_mtime
    except Exception:
        mtime = None

    # If cache missing or file changed on disk, reload
    if _cache is None or (_cache_mtime is not None and mtime is not None and mtime != _cache_mtime) or (_cache_mtime is None and mtime is not None):
        raw = yaml.safe_load(RULES_FILE.read_text(encoding="utf-8")) or {}
        # Interpolate placeholders in the rules using values from the default section.
        try:
            default = raw.get("default", {}) or {}
            flat = _flatten(default)
            # also expose top-level default keys without prefix
            flat.update({k: v for k, v in default.items() if not isinstance(v, dict)})
            _cache = _interpolate_strings(raw, flat)
        except Exception:
            _cache = raw
        _cache_mtime = mtime
        try:
            import logging
            logging.debug(f"rules_loader: loaded rules from {RULES_FILE} (mtime={_cache_mtime})")
        except Exception:
            pass
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
    global _cache_mtime
    _cache = None
    _cache_mtime = None
