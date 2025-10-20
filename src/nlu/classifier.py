from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import difflib
import unicodedata


def _normalize(text: str) -> str:
    if not text:
        return ""
    t = text.lower().strip()
    # Remover acentos
    t = unicodedata.normalize('NFKD', t)
    t = ''.join(c for c in t if not unicodedata.combining(c))
    return t


@dataclass
class IntentMatch:
    name: str
    action: str
    score: float
    intent_cfg: Dict[str, Any]


class SimpleNLU:
    """Clasificador NLU sencillo pero más robusto: normaliza, soporta coincidencia fuzzy y umbral.

    Config esperada en rules.nlu:
      - threshold: float (0-1) para aceptar una intención
      - low_confidence_message: str para orientar al usuario cuando la confianza es baja
      - intents: lista de intents con 'name', 'patterns', 'action', 'target' (opcional)
    """

    def __init__(self, nlu_cfg: Dict[str, Any]):
        self.cfg = nlu_cfg or {}
        self.threshold = float(self.cfg.get('threshold') or 0.75)

    def classify(self, text: str) -> Tuple[Optional[IntentMatch], float]:
        t = _normalize(text)
        best: Optional[IntentMatch] = None
        best_score = 0.0
        intents = list(self.cfg.get('intents') or [])
        for intent in intents:
            name = intent.get('name') or ''
            action = (intent.get('action') or '').lower()
            patterns = [ _normalize(str(p)) for p in (intent.get('patterns') or []) ]
            score = self._max_similarity(t, patterns)
            if score > best_score:
                best_score = score
                best = IntentMatch(name=name, action=action, score=score, intent_cfg=intent)
        return best, best_score

    @staticmethod
    def _max_similarity(text: str, patterns: List[str]) -> float:
        if not text or not patterns:
            return 0.0
        # Similaridad sobre cada patrón
        scores = [difflib.SequenceMatcher(a=text, b=p).ratio() for p in patterns]
        return max(scores) if scores else 0.0
