"""
Telegram Bot для Padel Court
"""
import os
from dotenv import load_dotenv
load_dotenv()

import logging
from telegram import Update, KeyboardButton, WebAppInfo, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:5000')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        "🎾 <b>Padel Court - Бронирование корта</b>\n\n"
        "Нажмите кнопку ниже чтобы открыть:",
        parse_mode='HTML',
        reply_markup=KeyboardButton(
            text="🎾 Играть",
            web_app=WebAppInfo(f"{WEBAPP_URL}/?user_id={user_id}")
        )
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 <b>Инструкция:</b>\n\n"
        f"1. Откройте: <code>{WEBAPP_URL}</code>\n"
        "2. Войдите через Telegram\n"
        "3. Создайте или присоединитесь к игре\n\n"
        "⚠️ Ограничения:\n"
        "• 1 активная игра на игрока\n"
        "• 1 создание игры на человека",
        parse_mode='HTML'
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    logger.info("Bot started")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()