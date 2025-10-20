from pathlib import Path
from src.storage.repository import TicketRepository


def test_repo_create_and_get(tmp_path: Path):
    repo = TicketRepository(tmp_path)
    t = repo.create("u1", "texto")
    got = repo.get(t["id"])
    assert got and got["id"] == t["id"]
