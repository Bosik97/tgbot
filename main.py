import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import BOT_TOKEN, ADMIN_ID
from database import init_db
from notifications import schedule_all_notifications
from handlers import register_handlers

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def on_startup():
    init_db()
    schedule_all_notifications(bot)
    try:
        await bot.send_message(ADMIN_ID, "Bot started and scheduler is active.")
    except Exception:
        pass

async def main():
    init_db()
    register_handlers(dp)
    dp.startup.register(on_startup)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())