import asyncio
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.bot_core.manager import BotManager

def print_log(msg):
    print(msg)

async def simulate_connector(text, user='debug_user', group='g1'):
    bot = BotManager()
    payload = {"text": text, "platform": "whatsapp", "platform_user_id": user, "group_id": group}
    print_log(f"\n--- Simulación webhook WhatsApp: {json.dumps(payload, ensure_ascii=False)}")
    res = bot.process_message(payload) or {}
    print_log(f"Manager response: {json.dumps(res, ensure_ascii=False, indent=2)}")
    # Simular lógica del conector WhatsApp
    if res.get('messages') and isinstance(res.get('messages'), list):
        for idx, m in enumerate(res['messages']):
            d = 0
            try:
                d = float(m.get('delay', 0) or 0)
            except Exception:
                d = 0
            text_to_send = str(m.get('text') or '')
            print_log(f"Sending reply to {user}: {text_to_send}")
            if d > 0:
                print_log(f"Delaying {d}s before sending next message to {user}")
                await asyncio.sleep(min(d, 1))
    elif res.get('text'):
        print_log(f"Sending reply to {user}: {res['text']}")
    else:
        print_log("No response to send")

async def main():
    await simulate_connector('/start')
    await simulate_connector('Hola')
    await simulate_connector('men')

if __name__ == '__main__':
    asyncio.run(main())
