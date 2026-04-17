import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# === ТОКЕНЫ (можно оставить hardcoded пока) ===
BOT_TOKEN = "8618587406:AAFQI1WhoE3YGH2Y3OWCp1TbQLQCin2qcyc"
API_FOOTBALL_KEY = "5eb43e41f2467478ff545e7f458f7975"
ADMIN_ID = 8618587406

logging.basicConfig(level=logging.INFO)

print("=== BOT STARTING ===")
print("Token loaded:", bool(BOT_TOKEN))

# Правильная инициализация бота для aiogram 3.13+
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

# Простой старт для теста
@dp.message(commands=["start"])
async def cmd_start(message):
    await message.answer(
        "✅ <b>Бот запущен успешно!</b>\n\n"
        "Привет! ⚽ Я твой помощник по матчам.\n"
        "Выбери язык:"
    )

async def on_startup():
    try:
        await bot.send_message(ADMIN_ID, "✅ Бот успешно запущен на Railway!")
        print("✅ Сообщение администратору отправлено")
    except Exception as e:
        print("Не удалось отправить сообщение админу:", e)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    dp.startup.register(on_startup)
    print("🚀 Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
