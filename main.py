import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import F

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

# ====================== ХЕНДЛЕРЫ ======================
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "✅ <b>Бот запущен!</b>\n\n"
        "⚽ Добро пожаловать в <b>Football Match Reminder</b>\n\n"
        "Сначала выбери язык:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
            [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kk")],
            [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]
        ])
    )

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):
    lang = callback.data[5:]
    await callback.message.edit_text(f"✅ Язык выбран: {'Русский' if lang=='ru' else 'Қазақша' if lang=='kk' else 'English'}")
    await callback.message.answer("Напиши город, в котором ты живёшь (например: Алматы, Москва, Астана):")

print("🚀 Бот запущен...")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
