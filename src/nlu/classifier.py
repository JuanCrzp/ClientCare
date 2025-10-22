from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import difflib
import unicodedata
import math
import pickle
from pathlib import Path
from datetime import datetime
import hashlib


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


class MLNLU:
    """Clasificador NLU con Machine Learning puro (sin dependencias externas pesadas).

    Implementa un Multinomial Naive Bayes con n-gramas de caracteres y palabras.
    - Entrena a partir de rules.nlu.intents.patterns
    - Serializa modelo en data/models/nlu_nb.pkl
    - Usa un umbral de confianza configurable (rules.nlu.threshold)

    Config opcional en rules.nlu.ml:
      - model_path: ruta del archivo de modelo (por defecto data/models/nlu_nb.pkl)
      - retrain_on_start: bool (False) para reentrenar siempre desde rules
      - char_ngrams: [3,5] rango n-gramas de caracteres
      - word_ngrams: [1,2] rango n-gramas de palabras
      - alpha: 1.0 suavizado Laplace
    """

    def __init__(self, nlu_cfg: Dict[str, Any], data_dir: str | Path = "data"):
        self.cfg = nlu_cfg or {}
        self.threshold = float(self.cfg.get("threshold") or 0.75)
        self.ml_cfg = dict(self.cfg.get("ml") or {})
        self.model_path = Path(self.ml_cfg.get("model_path") or Path(data_dir) / "models" / "nlu_nb.pkl")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.char_ng = tuple(self.ml_cfg.get("char_ngrams") or (3, 5))
        self.word_ng = tuple(self.ml_cfg.get("word_ngrams") or (1, 2))
        self.alpha = float(self.ml_cfg.get("alpha") or 1.0)
        self._model: Optional[dict] = None

        retrain = bool(self.ml_cfg.get("retrain_on_start", False))
        if retrain or not self.model_path.exists():
            trained = self._train_from_rules()
            if trained:
                self._save()
        else:
            self._load()

    # =============== API principal ===============
    def classify(self, text: str) -> Tuple[Optional[IntentMatch], float]:
        if not self._model:
            # Si no hay modelo (reglas insuficientes), devolvemos None con score 0
            return None, 0.0
        t = _normalize(text)
        # Extrae características
        feats = self._extract_features(t)
        # Si no hay ningún n-gram conocido, no hay confianza
        if not feats:
            return None, 0.0
        # Vectoriza
        scores = {}
        for label in self._model["labels"]:
            logprior = self._model["logpriors"].get(label, -1e9)
            loglik = 0.0
            class_log_probs = self._model["log_probs"].get(label) or {}
            for f, c in feats.items():
                lp = class_log_probs.get(f)
                if lp is not None:
                    loglik += c * lp
            scores[label] = logprior + loglik

        # Softmax para convertir a pseudo-probabilidades
        max_log = max(scores.values())
        exp_scores = {k: math.exp(v - max_log) for k, v in scores.items()}
        total = sum(exp_scores.values()) or 1.0
        probs = {k: v / total for k, v in exp_scores.items()}
        best_label = max(probs, key=probs.get)
        best_prob = probs[best_label]

        # Mapear a intent config
        intents = list(self.cfg.get("intents") or [])
        intent_map = {i.get("name"): i for i in intents}
        matched_cfg = intent_map.get(best_label)

        # Heurística: si el texto no contiene ningún token conocido de ese intent, bajar confianza
        # (ya reducimos si no hay feats en absoluto). Aquí podríamos comparar cobertura de features.
        if best_prob < 1.0 and len(feats) < 2:
            best_prob *= 0.85

        if not matched_cfg:
            return None, 0.0

        match = IntentMatch(
            name=best_label,
            action=(matched_cfg.get("action") or "").lower(),
            score=best_prob,
            intent_cfg=matched_cfg,
        )
        return match, best_prob

    # =============== Entrenamiento ===============
    def _train_from_rules(self) -> bool:
        intents = list(self.cfg.get("intents") or [])
        # Construir dataset a partir de patterns
        X: list[str] = []
        y: list[str] = []
        for intent in intents:
            name = intent.get("name")
            pats = [p for p in (intent.get("patterns") or []) if isinstance(p, str) and p.strip()]
            for p in pats:
                X.append(_normalize(p))
                y.append(name)
        # Necesitamos al menos 2 clases con muestras
        labels = sorted(set(y))
        if len(labels) < 2:
            self._model = None
            return False
        # Construir vocabulario de n-gramas
        vocab: Dict[str, int] = {}
        def add_feat(f: str):
            if f not in vocab:
                vocab[f] = len(vocab)
        for txt in X:
            feats = self._extract_features(txt, build_vocab=True, _vocab=vocab)
            # acceso para forzar creación en vocab
            _ = feats
        # Contabilizar por clase
        class_counts: Dict[str, Dict[str, int]] = {lbl: {} for lbl in labels}
        total_counts: Dict[str, int] = {lbl: 0 for lbl in labels}
        for txt, lbl in zip(X, y):
            feats = self._extract_features(txt, build_vocab=False, _vocab=vocab)
            for f, c in feats.items():
                class_counts[lbl][f] = class_counts[lbl].get(f, 0) + c
                total_counts[lbl] += c

        # Calcular log-probabilidades con suavizado de Laplace
        V = len(vocab)
        alpha = self.alpha
        log_probs: Dict[str, Dict[str, float]] = {lbl: {} for lbl in labels}
        for lbl in labels:
            denom = total_counts[lbl] + alpha * V
            for f in vocab.keys():
                count = class_counts[lbl].get(f, 0)
                prob = (count + alpha) / denom
                log_probs[lbl][f] = math.log(prob)
        # Priors uniformes o proporcionales a ejemplos
        label_freq = {lbl: 0 for lbl in labels}
        for lbl in y:
            label_freq[lbl] += 1
        total_docs = len(y)
        logpriors = {lbl: math.log((label_freq[lbl] / total_docs) if total_docs else (1.0 / len(labels))) for lbl in labels}

        # Checksum de intents/patterns para trazabilidad
        checksum_src = []
        for intent in intents:
            name = str(intent.get("name") or "")
            pats = [str(p) for p in (intent.get("patterns") or [])]
            checksum_src.append(name + "::" + "|".join(sorted(pats)))
        checksum = hashlib.sha256("\n".join(sorted(checksum_src)).encode("utf-8")).hexdigest()

        # Metadatos
        meta = {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "examples_total": total_docs,
            "labels_total": len(labels),
            "examples_per_label": label_freq,
            "vocab_size": V,
            "char_ngrams": self.char_ng,
            "word_ngrams": self.word_ng,
            "alpha": alpha,
            "threshold": self.threshold,
            "checksum": checksum,
            "version": 1,
        }

        self._model = {
            "labels": labels,
            "vocab": vocab,
            "log_probs": log_probs,
            "logpriors": logpriors,
            "char_ng": self.char_ng,
            "word_ng": self.word_ng,
            "alpha": alpha,
            "meta": meta,
        }
        return True

    # =============== Persistencia ===============
    def _save(self) -> None:
        if not self._model:
            return
        try:
            with open(self.model_path, "wb") as f:
                pickle.dump(self._model, f)
        except Exception:
            # Si falla el guardado, continuamos con el modelo en memoria
            pass

    def _load(self) -> None:
        try:
            with open(self.model_path, "rb") as f:
                self._model = pickle.load(f)
        except Exception:
            self._model = None

    # =============== Feature extraction ===============
    def _extract_features(
        self,
        text: str,
        build_vocab: bool = False,
        _vocab: Optional[Dict[str, int]] = None,
    ) -> Dict[str, int]:
        """Extrae n-gramas de caracteres y palabras como características discretas.
        Si build_vocab=True, también rellena el vocab.
        """
        text = text or ""
        feats: Dict[str, int] = {}

        def add_feat(tok: str):
            if not tok:
                return
            if build_vocab and _vocab is not None and tok not in _vocab:
                _vocab[tok] = len(_vocab)
            if _vocab is None or tok in _vocab:
                feats[tok] = feats.get(tok, 0) + 1

        # n-gramas de caracteres
        cmin, cmax = self.char_ng
        n = len(text)
        for k in range(max(1, cmin), max(cmin, cmax) + 1):
            if k > n:
                continue
            for i in range(n - k + 1):
                add_feat(f"c:{text[i:i+k]}")

        # n-gramas de palabras
        words = [w for w in text.split() if w]
        wmin, wmax = self.word_ng
        W = len(words)
        for k in range(max(1, wmin), max(wmin, wmax) + 1):
            if k > W:
                continue
            for i in range(W - k + 1):
                add_feat("w:" + "_".join(words[i:i+k]))

        return feats
