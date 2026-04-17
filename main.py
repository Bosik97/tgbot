import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# === ЖЁСТКО ПРОПИСЫВАЕМ ТОКЕН ДЛЯ ТЕСТА ===
BOT_TOKEN = "8618587406:AAFQI1WhoE3YGH2Y3OWCp1TbQLQCin2qcyc"
API_FOOTBALL_KEY = "5eb43e41f2467478ff545e7f458f7975"
ADMIN_ID = 8618587406

logging.basicConfig(level=logging.INFO)

print("=== DEBUG ENVIRONMENT ===")
print("BOT_TOKEN loaded:", bool(BOT_TOKEN))
print("=================================")

# Правильная инициализация бота для aiogram 3.13+
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

async def on_startup():
    await bot.send_message(ADMIN_ID, "✅ Бот успешно запущен и работает!")
    print("✅ Бот успешно запущен!")

@dp.message(commands=["start"])
async def start(message):
    await message.answer("Привет! ⚽\nВыбери язык:", reply_markup=language_kb())  # клавиатура позже

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
