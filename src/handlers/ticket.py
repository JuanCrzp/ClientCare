from pathlib import Path
from ..app.config import settings
from ..storage.repository import TicketRepository
from ..config.rules_loader import get_rules_for

_repo = TicketRepository(Path(settings.data_dir))

def open_ticket(user_id: str, text: str, chat_id: str | None = None) -> str:
    t = _repo.create(user_id, text)
    rules = get_rules_for(chat_id)
    template = rules.get("tickets", {}).get("message_opened") or "He creado tu ticket #{ticket_id}."
    msg = template.replace("#{ticket_id}", str(t["id"]))
    return f"{msg} Puedes consultar con /ticket {t['id']}"
