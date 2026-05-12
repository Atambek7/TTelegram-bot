import asyncio
import logging
import os
from threading import Thread
from flask import Flask

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message

from config import BOT_TOKEN
from handlers import all_routers
from keyboards import reply_menu_kb

logging.basicConfig(level=logging.INFO)

# ---------------- FLASK ----------------

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

def keep_alive():
    t = Thread(target=run_web)
    t.start()

# ---------------- BOT ----------------

async def cmd_cancel(message: Message):
    await message.answer(
        "✅ Action cancelled. You're back to the main menu.",
        reply_markup=reply_menu_kb(),
        parse_mode="HTML"
    )

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()

    dp.message.register(cmd_cancel, Command("cancel"))

    for router in all_routers:
        dp.include_router(router)

    logging.info("Bot started!")

    await dp.start_polling(bot)

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())
