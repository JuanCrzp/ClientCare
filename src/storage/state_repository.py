from __future__ import annotations

from pathlib import Path
import json
from typing import Optional, Dict, Any


class StateRepository:
    """Almacena el estado de conversación por usuario y chat.

    Persistencia simple en archivo JSON: {"<chat_id>|<user_id>": {"name": str, "data": dict}}
    """

    def __init__(self, data_dir: Path):
        self.dir = data_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file = self.dir / "state.json"
        if not self.file.exists():
            self.file.write_text("{}", encoding="utf-8")

    def _load(self) -> Dict[str, Any]:
        try:
            return json.loads(self.file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self, data: Dict[str, Any]) -> None:
        self.file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _key(user_id: str, chat_id: Optional[str]) -> str:
        return f"{chat_id or '-'}|{user_id or '-'}"

    def get(self, user_id: str, chat_id: Optional[str]) -> Dict[str, Any]:
        data = self._load()
        return data.get(self._key(user_id, chat_id), {}) or {}

    def set(self, user_id: str, chat_id: Optional[str], name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        data = self._load()
        data[self._key(user_id, chat_id)] = {"name": name, "data": payload or {}}
        self._save(data)

    def update_field(self, user_id: str, chat_id: Optional[str], field: str, value: Any) -> None:
        """Actualizar un campo dentro del objeto data para el estado del usuario.

        Útil para marcar flags como 'greet_shown'.
        """
        data = self._load()
        k = self._key(user_id, chat_id)
        cur = data.get(k) or {}
        cur_data = cur.get("data") or {}
        cur_data[field] = value
        cur["data"] = cur_data
        data[k] = cur
        self._save(data)

    def clear(self, user_id: str, chat_id: Optional[str]) -> None:
        data = self._load()
        k = self._key(user_id, chat_id)
        if k in data:
            del data[k]
            self._save(data)
