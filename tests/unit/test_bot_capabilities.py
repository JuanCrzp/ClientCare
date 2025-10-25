from src.handlers.faq import answer_faq

def test_bot_capabilities():
    resp = answer_faq("qué puedes hacer?")
    assert resp is not None
    assert "Puedo" in resp
    # Debe mencionar al menos una función activa
    assert any(palabra in resp for palabra in ["catálogo", "menú", "soporte", "preguntas"])
    print("Respuesta generada:", resp)

if __name__ == "__main__":
    test_bot_capabilities()
