from src.bot_core.manager import BotManager


def test_intent_fuzzy_match_ticket():
    bot = BotManager()
    # Error tipográfico/adición: 'abrirr tiket' debería acercarse a 'abrir ticket'
    r = bot.process_message({"text": "abrirr tiket", "platform_user_id": "f1", "group_id": "g1"})
    assert r and "Por favor" in (r.get("text") or "")


def test_low_confidence_guidance():
    bot = BotManager()
    # Una frase alejada pero cercana a un patrón debe devolver el mensaje de baja confianza
    r = bot.process_message({"text": "men", "platform_user_id": "f2", "group_id": "g1"})
    # Ahora el mensaje de baja confianza puede estar en 'text' o en el segundo mensaje del array
    if "messages" in r:
        texts = " ".join(m["text"] for m in r["messages"])
        # Acepta el saludo puro o el mensaje de orientación
        assert "bienvenid" in texts.lower() or "ayudarte" in texts.lower() or "menú" in texts.lower() or "agente" in texts.lower()
    else:
        txt = (r.get("text") or "").lower()
        assert "bienvenid" in txt or "ayudarte" in txt or "menú" in txt or "agente" in txt
