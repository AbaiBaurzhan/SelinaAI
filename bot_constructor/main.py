# main.py
from __future__ import annotations
import os
from dotenv import load_dotenv
from openai import OpenAI

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
)

load_dotenv("touch.env") or load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
WEBAPP_URL     = os.getenv("WEBAPP_URL", "http://127.0.0.1:8000")
OPENAI_KEY     = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN не задан в touch.env")

def system_prompt_from_env() -> str:
    # На этапе MVP системный промпт берём из базы веб‑панели (API) — здесь запасной вариант:
    return os.getenv("FALLBACK_SYSTEM_PROMPT", "Ты вежливый ассистент малого бизнеса.")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔧 Открыть панель", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await update.message.reply_text(
        "Привет! Я конструктор ИИ‑ассистента.\n"
        "Нажми кнопку, чтобы открыть панель и пройти быстрый мастер.",
        reply_markup=kb
    )

async def panel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔧 Открыть панель настроек", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await update.message.reply_text("Открой панель настроек в мини‑приложении.", reply_markup=kb)

async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрый тест ответа ассистента прямо в чате."""
    if not context.args:
        return await update.message.reply_text("Использование: /ask ваш вопрос")
    question = " ".join(context.args)

    key = OPENAI_KEY
    if not key:
        return await update.message.reply_text("Нет OPENAI_API_KEY в окружении.")
    client = OpenAI(api_key=key)

    await update.message.chat.send_action(ChatAction.TYPING)
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt_from_env()},
                {"role": "user", "content": question},
            ],
            temperature=0.4,
        )
        answer = resp.choices[0].message.content
        await update.message.reply_text(f"🤖 {answer}")
    except Exception as e:
        await update.message.reply_text(f"Ошибка OpenAI: {e}")

async def fallback_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_cmd(update, context)

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("panel", panel_cmd))
    app.add_handler(CommandHandler("ask", ask_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text))
    print("🤖 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
