from pathlib import Path
import importlib
import json
from src.app import config as app_config


def make_manager_with_tmp(tmp_path):
    # Cambiar data_dir y recargar manager para que tome el nuevo directorio
    app_config.settings.data_dir = str(tmp_path)
    from src.bot_core import manager as m
    importlib.reload(m)
    return m


def test_offer_resume_and_history_command(tmp_path, monkeypatch):
    m = make_manager_with_tmp(tmp_path)
    BotManager = m.BotManager
    _conv = m._conv

    user = 'u42'
    chat = 'c99'

    # Primer mensaje: inicia conversación
    payload = {"text": "hola", "platform_user_id": user, "group_id": chat}
    resp = BotManager().process_message(payload)
    assert isinstance(resp, dict)

    # Establecer un tema pendiente
    _conv.set_topic(user, chat, name='ticket_pendiente', ttl_days=14)

    # Simular que pasó más de resume_after (60 min por defecto)
    # Tocamos el último evento de historial para retrocederlo 2 horas
    conv_file = Path(tmp_path) / 'conversations.json'
    if conv_file.exists():
        data = json.loads(conv_file.read_text(encoding='utf-8'))
        key = f"{chat}|{user}"
        if key in data and 'history' in data[key] and data[key]['history']:
            data[key]['history'][-1]['ts'] -= (2 * 3600)
            conv_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

    # Segundo mensaje: debe ofrecer retomar el tema
    resp2 = BotManager().process_message({"text": "hola", "platform_user_id": user, "group_id": chat})
    assert 'pendiente' in (resp2.get('text') or '').lower()

    # Comando /historial debe devolver líneas
    hist = BotManager().process_message({"text": "/historial", "platform_user_id": user, "group_id": chat})
    assert isinstance(hist, dict) and ('[' in hist.get('text', ''))
