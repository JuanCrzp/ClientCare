from src.bot_core.manager import BotManager


def test_menu_start():
    bot = BotManager()
    res = bot.process_message({"text": "/start", "platform_user_id": "u1", "group_id": "g1"})
    assert res and "text" in res


def test_faq_match():
    bot = BotManager()
    res = bot.process_message({"text": "precios", "platform_user_id": "u1", "group_id": "g1"})
    assert res and "text" in res


def test_menu_to_faq_submenu():
    bot = BotManager()
    # Abrir menú principal
    r1 = bot.process_message({"text": "/start", "platform_user_id": "u2", "group_id": "g1"})
    assert r1 and "text" in r1
    # Elegir FAQ (opción 1)
    r2 = bot.process_message({"text": "1", "platform_user_id": "u2", "group_id": "g1"})
    assert r2 and "Submenú" in (r2.get("text") or "")
    # Consultar algo del FAQ en submenú
    r3 = bot.process_message({"text": "planes", "platform_user_id": "u2", "group_id": "g1"})
    assert r3 and "text" in r3


def test_ticket_guided_flow():
    bot = BotManager()
    # Opción 2 desde menú
    bot.process_message({"text": "/start", "platform_user_id": "u3", "group_id": "g1"})
    r2 = bot.process_message({"text": "2", "platform_user_id": "u3", "group_id": "g1"})
    assert r2 and "Por favor" in (r2.get("text") or "")
    # Enviar detalle para crear ticket
    r3 = bot.process_message({"text": "Mi app falla al iniciar", "platform_user_id": "u3", "group_id": "g1"})
    assert r3 and "ticket" in (r3.get("text") or "").lower()


def test_intents_open_ticket():
    bot = BotManager()
    r = bot.process_message({"text": "quiero abrir ticket", "platform_user_id": "u4", "group_id": "g1"})
    assert r and "Por favor" in (r.get("text") or "")


def test_intents_goto_faq():
    bot = BotManager()
    r = bot.process_message({"text": "ver menu", "platform_user_id": "u5", "group_id": "g1"})
    # Puede llevar al main o a faq según intent, verificamos que responda algo
    assert r and "text" in r
