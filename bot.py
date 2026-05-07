import logging
import os
import httpx
from threading import Thread
from flask import Flask
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ParseMode
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)

# Настройки OpenRouter
API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Бесплатная модель DeepSeek: deepseek/deepseek-r1:free
MODEL = "deepseek/deepseek-r1:free"

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("👋 Привет! Я бот с искусственным интеллектом. Просто напиши мне любое сообщение, и я отвечу с помощью ИИ!")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def ai_chat(message: types.Message):
    user_prompt = message.text.strip()
    if not user_prompt:
        await message.reply("Пожалуйста, напиши текстовое сообщение.")
        return

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "https://my-ai-bot-1-2kbq.onrender.com",  # адрес твоего сервиса
        "X-Title": "My Telegram AI Bot",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.7
    }

    thinking_msg = await message.reply("⌛ Думаю...")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            ai_text = data["choices"][0]["message"]["content"]
            await bot.delete_message(chat_id=message.chat.id, message_id=thinking_msg.message_id)
            await message.answer(ai_text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=thinking_msg.message_id,
            text=f"❌ Ошибка: {e}"
        )

# Flask-сервер
app = Flask(__name__)

@app.route('/')
def index():
    return "Бот работает!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    executor.start_polling(dp, skip_updates=True)
