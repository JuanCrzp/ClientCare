from pathlib import Path
from src.storage.conversation_repository import ConversationRepository


def test_history_limit_and_topic_ttl(tmp_path, monkeypatch):
    data_dir = Path(tmp_path)
    repo = ConversationRepository(data_dir)

    # Fijar tiempo controlado
    t0 = 1_700_000_000
    monkeypatch.setattr('time.time', lambda: t0)

    user = 'u1'
    chat = 'c1'

    # Insertar más de 5 eventos y limitar a 5
    for i in range(10):
        repo.append_event(user, chat, role='user', text=f'msg {i}', max_items=5)

    hist = repo.get_history(user, chat, limit=100)
    assert len(hist) == 5
    assert hist[0]['text'] == 'msg 5'
    assert hist[-1]['text'] == 'msg 9'

    # Topic con TTL y expiración
    repo.set_topic(user, chat, name='tema_pendiente', ttl_days=1)
    assert repo.get_topic(user, chat) is not None

    # Avanzar 2 días
    monkeypatch.setattr('time.time', lambda: t0 + 2 * 86400)
    assert repo.get_topic(user, chat) is None
