import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_ID
from database import *
from notifications import schedule_all_notifications
from handlers import register_handlers

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()

async def on_startup():
    await bot.send_message(ADMIN_ID, "✅ Бот успешно запущен!")
    schedule_all_notifications(bot)

async def main():
    register_handlers(dp)
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
