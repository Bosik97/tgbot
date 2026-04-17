import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = "8618587406:AAFQI1WhoE3YGH2Y3OWCp1TbQLQCin2qcyc"
API_FOOTBALL_KEY = "5eb43e41f2467478ff545e7f458f7975"
ADMIN_ID = 8618587406
# ===================================================

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# ===================== ХЕНДЛЕРЫ =====================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "✅ <b>Бот успешно запущен!</b>\n\n"
        "⚽ Добро пожаловать в Football Match Reminder!\n\n"
        "Напиши /start ещё раз после полной настройки."
    )

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Пока доступны только /start и /help")

# ====================================================

async def on_startup():
    try:
        await bot.send_message(ADMIN_ID, "✅ <b>Бот успешно запущен на Railway!</b>")
        print("✅ Сообщение администратору отправлено")
    except Exception as e:
        print("Не удалось отправить сообщение админу:", e)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    print("🚀 Бот запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
