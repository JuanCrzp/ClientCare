from __future__ import annotations

from pathlib import Path
import json
import time
from typing import Any, Dict, List, Optional


class ConversationRepository:
    """Almacena historial de conversación y temas abiertos por usuario y chat.

    Estructura JSON:
    {
      "<chat>|<user>": {
        "history": [ {"ts": 1700000000.0, "role": "user|bot", "text": str, "meta": {...}} ],
        "topic": {"name": str, "data": {...}, "ts": float, "expires_at": float | null},
        "last_active": float
      }
    }

    Diseñado para ser migrable a DB (MySQL) reemplazando este repositorio.
    """

    def __init__(self, data_dir: Path, filename: str = "conversations.json"):
        self.dir = data_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file = self.dir / filename
        if not self.file.exists():
            self.file.write_text("{}", encoding="utf-8")

    @staticmethod
    def _key(user_id: str, chat_id: Optional[str]) -> str:
        return f"{chat_id or '-'}|{user_id or '-'}"

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        self.file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def append_event(self, user_id: str, chat_id: Optional[str], role: str, text: str, meta: Optional[Dict[str, Any]] = None, max_items: int = 100) -> None:
        data = self._load()
        k = self._key(user_id, chat_id)
        cur = data.get(k) or {}
        history: List[Dict[str, Any]] = list(cur.get("history") or [])
        history.append({
            "ts": time.time(),
            "role": role,
            "text": text,
            "meta": meta or {}
        })
        # limitar historial
        if max_items > 0 and len(history) > max_items:
            history = history[-max_items:]
        cur["history"] = history
        cur["last_active"] = time.time()
        data[k] = cur
        self._save(data)

    def get_history(self, user_id: str, chat_id: Optional[str], limit: int = 20) -> List[Dict[str, Any]]:
        d = self._load().get(self._key(user_id, chat_id)) or {}
        hist: List[Dict[str, Any]] = list(d.get("history") or [])
        if limit > 0:
            return hist[-limit:]
        return hist

    def clear_history(self, user_id: str, chat_id: Optional[str]) -> None:
        data = self._load()
        k = self._key(user_id, chat_id)
        cur = data.get(k) or {}
        cur["history"] = []
        data[k] = cur
        self._save(data)

    def set_topic(self, user_id: str, chat_id: Optional[str], name: str, topic_data: Optional[Dict[str, Any]] = None, ttl_days: Optional[int] = None) -> None:
        now = time.time()
        expires_at = None
        if isinstance(ttl_days, int) and ttl_days > 0:
            expires_at = now + ttl_days * 86400
        data = self._load()
        k = self._key(user_id, chat_id)
        cur = data.get(k) or {}
        cur["topic"] = {
            "name": name,
            "data": topic_data or {},
            "ts": now,
            "expires_at": expires_at,
        }
        cur["last_active"] = now
        data[k] = cur
        self._save(data)

    def get_topic(self, user_id: str, chat_id: Optional[str]) -> Optional[Dict[str, Any]]:
        cur = self._load().get(self._key(user_id, chat_id)) or {}
        topic = cur.get("topic")
        if not topic:
            return None
        # si expiró, limpiarlo
        exp = topic.get("expires_at")
        if isinstance(exp, (int, float)) and exp > 0 and time.time() > float(exp):
            self.clear_topic(user_id, chat_id)
            return None
        return topic

    def clear_topic(self, user_id: str, chat_id: Optional[str]) -> None:
        data = self._load()
        k = self._key(user_id, chat_id)
        cur = data.get(k) or {}
        if "topic" in cur:
            del cur["topic"]
        data[k] = cur
        self._save(data)
