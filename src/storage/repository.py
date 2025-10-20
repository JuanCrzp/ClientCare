from pathlib import Path
import json
from typing import Optional

class TicketRepository:
    def __init__(self, data_dir: Path):
        self.dir = data_dir
        self.dir.mkdir(parents=True, exist_ok=True)
        self.file = self.dir / "tickets.json"
        if not self.file.exists():
            self.file.write_text("[]", encoding="utf-8")

    def _load(self):
        return json.loads(self.file.read_text(encoding="utf-8"))

    def _save(self, data):
        self.file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def create(self, user_id: str, text: str) -> dict:
        data = self._load()
        ticket_id = len(data) + 1
        ticket = {"id": ticket_id, "user_id": user_id, "text": text, "status": "open"}
        data.append(ticket)
        self._save(data)
        return ticket

    def get(self, ticket_id: int) -> Optional[dict]:
        data = self._load()
        for t in data:
            if t.get("id") == ticket_id:
                return t
        return None
