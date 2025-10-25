import asyncio
import json
import os
import sys

# Ajustar path si se ejecuta desde scripts
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.bot_core.manager import BotManager  # noqa: E402

async def simulate_once(text, user='debug_user', group='g1'):
    bot = BotManager()
    payload = {"text": text, "platform_user_id": user, "group_id": group}
    print('\n--- Simulación de webhook: payload=')
    print(json.dumps(payload, ensure_ascii=False))
    res = bot.process_message(payload) or {}
    print('\nManager devolvió:')
    print(json.dumps(res, ensure_ascii=False, indent=2))

    # Simular conector: respetar messages/delay
    if res.get('messages') and isinstance(res.get('messages'), list):
        for idx, m in enumerate(res.get('messages')):
            d = 0
            try:
                d = float(m.get('delay', 0) or 0)
            except Exception:
                d = 0
            if d > 0:
                print(f"(simulado) Esperando {d}s antes de enviar mensaje #{idx+1}")
                # usar un delay corto para pruebas (limitar a 1s)
                await asyncio.sleep(min(d, 1))
            text_to_send = str(m.get('text') or '')
            print(f"(simulado) Enviando mensaje #{idx+1} a {user}: {text_to_send}")
    elif res.get('text'):
        print(f"(simulado) Enviando mensaje único a {user}: {res.get('text')}")
    else:
        print('(simulado) No hay respuesta para enviar')

async def main():
    # Probar /start
    await simulate_once('/start')
    # Probar saludo corto 'hola'
    await simulate_once('Hola')
    # Probar otra prueba que antes fallaba
    await simulate_once('men')

if __name__ == '__main__':
    asyncio.run(main())
