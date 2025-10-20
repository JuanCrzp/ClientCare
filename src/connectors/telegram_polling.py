import os
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from telegram import Update
from ..bot_core.manager import BotManager
from ..storage.repository import TicketRepository
from ..app.config import settings

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
TOKEN = os.getenv("TELEGRAM_TOKEN", "")
BOT_NAME = os.getenv("TELEGRAM_BOT_NAME", "AtencionClienteBot")

manager = BotManager()
repo = TicketRepository(Path(settings.data_dir))

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Validaciones para evitar None en atributos opcionales
    if update.effective_user is None or update.effective_chat is None or update.message is None:
        return
    payload = {
        "platform": "telegram",
        "platform_user_id": str(update.effective_user.id),
        "group_id": str(update.effective_chat.id),
        "text": "/start",
    }
    resp = manager.process_message(payload) or {}
    if resp.get("text") and update.message is not None:
        await update.message.reply_text(resp["text"])

async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None or update.effective_chat is None:
        return
    text = update.message.text or ""
    payload = {
        "platform": "telegram",
        "platform_user_id": str(update.effective_user.id),
        "group_id": str(update.effective_chat.id),
        "text": text,
    }
    resp = manager.process_message(payload) or {}
    if resp.get("text") and update.message is not None:
        await update.message.reply_text(resp["text"])

async def cmd_reload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from ..config.rules_loader import reload_rules_cache
    reload_rules_cache()
    if update.message is not None:
        await update.message.reply_text("Reglas recargadas.")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is not None:
        await update.message.reply_text("Comandos: /start, /help, /reload")

async def cmd_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    args = context.args or []
    if not args:
        await update.message.reply_text("Uso: /ticket <id>")
        return
    try:
        tid = int(args[0])
    except Exception:
        await update.message.reply_text("ID inválido.")
        return
    t = repo.get(tid)
    if not t:
        await update.message.reply_text("No encontré ese ticket.")
        return
    await update.message.reply_text(f"Ticket #{t['id']} - estado: {t['status']} - texto: {t['text']}")

def main():
    if not TOKEN:
        raise SystemExit("TELEGRAM_TOKEN no configurado")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("ticket", cmd_ticket))
    app.add_handler(CommandHandler("reload", cmd_reload))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    print(f"[{BOT_NAME}] Iniciado en modo polling")
    app.run_polling()

if __name__ == "__main__":
    main()
