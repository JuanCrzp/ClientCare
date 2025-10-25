import json
# time module removed; not used in this test file
from pathlib import Path
import importlib
from src.app import config as app_config
from src.config.rules_loader import get_rules
from src.utils.duration import parse_duration_to_seconds


def make_manager_with_tmp(tmp_path):
    app_config.settings.data_dir = str(tmp_path)
    from src.bot_core import manager as m
    importlib.reload(m)
    return m


def rewind_last_user_message(tmp_path: Path, user: str, chat: str, seconds: int):
    conv_file = Path(tmp_path) / 'conversations.json'
    if conv_file.exists():
        data = json.loads(conv_file.read_text(encoding='utf-8'))
        key = f"{chat}|{user}"
        if key in data:
            hist = data[key].get('history') or []
            # Buscar último evento del usuario
            for ev in reversed(hist):
                if ev.get('role') == 'user':
                    ev['ts'] -= seconds
                    break
            conv_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def test_inactivity_close_chat(tmp_path):
    m = make_manager_with_tmp(tmp_path)
    BotManager = m.BotManager
    user = 'u100'
    chat = 'c1'

    # Ir al menú y seleccionar opción 2 (ticket) para que el bot pida detalle
    BotManager().process_message({"text": "/start", "platform_user_id": user, "group_id": chat})
    resp1 = BotManager().process_message({"text": "2", "platform_user_id": user, "group_id": chat})
    # El bot ahora pide detalle; comprobamos una frase genérica para evitar roturas por cambios menores
    assert 'por favor' in (resp1.get('text') or '').lower()

    # Calcular close_after desde rules.yaml y rebobinar un poco más para forzar cierre
    from src.config.rules_loader import get_rules
    from src.utils.duration import parse_duration_to_seconds
    rules = get_rules().get('default', {})
    inactivity = (rules.get('memory') or {}).get('inactivity') or {}
    close_after = inactivity.get('close_after', '24h')
    close_s = parse_duration_to_seconds(close_after) or (24 * 3600)
    rewind_last_user_message(tmp_path, user, chat, seconds=close_s + 60)

    # Siguiente mensaje debe provocar cierre por inactividad
    resp2 = BotManager().process_message({"text": "hola", "platform_user_id": user, "group_id": chat})
    # Aceptamos cualquier indicación de cierre por inactividad
    assert 'cerr' in (resp2.get('text') or '').lower()


def test_inactivity_reminder_once(tmp_path):
    m = make_manager_with_tmp(tmp_path)
    BotManager = m.BotManager
    user = 'u101'
    chat = 'c2'

    # Ir al menú y seleccionar opción 2 (ticket) para que el bot pida detalle
    BotManager().process_message({"text": "/start", "platform_user_id": user, "group_id": chat})
    _ = BotManager().process_message({"text": "2", "platform_user_id": user, "group_id": chat})

    # Calcular tiempos desde rules y rebobinar para caer entre reminder_after y close_after
    rules = get_rules().get('default', {})
    inactivity = (rules.get('memory') or {}).get('inactivity') or {}
    rem_after = inactivity.get('reminder_after', '30m')
    close_after = inactivity.get('close_after', '24h')
    rem_s = parse_duration_to_seconds(rem_after) or (30 * 60)
    close_s = parse_duration_to_seconds(close_after) or (24 * 3600)
    delta = max(rem_s + 10, min(rem_s + 60, close_s - 60)) if close_s > rem_s else rem_s + 10
    rewind_last_user_message(tmp_path, user, chat, seconds=delta)

    # Debe enviar recordatorio
    resp2 = BotManager().process_message({"text": "hola", "platform_user_id": user, "group_id": chat})
    assert 'sigues ahí' in (resp2.get('text') or '').lower()

    # Rebobinar de nuevo 10 minutos y enviar otro mensaje: no debería repetir recordatorio (send_reminder_once)
    rewind_last_user_message(tmp_path, user, chat, seconds=10 * 60)
    resp3 = BotManager().process_message({"text": "hola", "platform_user_id": user, "group_id": chat})
    # No comprobamos el texto exacto, solo que no sea el recordatorio (puede ser menú/fallback)
    assert (resp3.get('text') or '').lower().find('sigues ahí') == -1
