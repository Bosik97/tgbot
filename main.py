import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "8618587406:AAFQI1WhoE3YGH2Y3OWCp1TbQLQCin2qcyc"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

async def main():
    from handlers import register_handlers
    from notifications import setup_scheduler
    
    register_handlers(dp)
    setup_scheduler(bot)
    
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот запущен полностью!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
