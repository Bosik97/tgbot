from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database import save_user, add_favorite, get_favorites, get_user
from utils import search_teams, get_fixtures, get_city_timezone
from keyboards import main_menu, language_kb
from notifications import send_match_notify, schedule_all_notifications
from config import LANGUAGES

router = Router()

def register_handlers(dp):
    dp.include_router(router)

@router.callback_query(F.data.startswith("lang_"))
async def choose_lang(callback: CallbackQuery):
    lang = callback.data[5:]
    save_user(callback.from_user.id, callback.from_user.username, lang)
    await callback.message.edit_text(f"✅ {LANGUAGES[lang]}")
    await callback.message.answer("Напиши свой город:")

@router.message()
async def main_handler(message: Message):
    user = get_user(message.from_user.id)
    text = message.text.strip()

    if not user or not user[3]:  # Нет города
        tz = await get_city_timezone(text)
        save_user(message.from_user.id, message.from_user.username, city=text, timezone=tz)
        await message.answer(f"✅ Город: <b>{text}</b>\n⏰ Таймзона: <b>{tz}</b>", reply_markup=main_menu('ru'))
        return

    lang = user[2]

    if any(x in text.lower() for x in ["добавить", "қосу", "add team"]):
        await message.answer("Напиши название команды:")
        return

    if any(x in text.lower() for x in ["мои команды", "менің", "my teams"]):
        favs = get_favorites(message.from_user.id)
        if not favs:
            await message.answer("У тебя пока нет любимых команд.")
        else:
            await message.answer("Твои команды:\n" + "\n".join([f"• {name}" for _, name in favs]))
        return

    # Поиск команд
    teams = await search_teams(text)
    if teams:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{t['team']['name']}", callback_data=f"add_{t['team']['id']}_{t['team']['name']}")]
            for t in teams
        ])
        await message.answer("Выбери команду из списка:", reply_markup=kb)
    else:
        await message.answer("Команда не найдена 😔 Попробуй другое название.")

@router.callback_query(F.data.startswith("add_"))
async def add_team(callback: CallbackQuery):
    _, team_id, team_name = callback.data.split("_", 2)
    add_favorite(callback.from_user.id, int(team_id), team_name)
    await callback.message.answer(f"✅ <b>{team_name}</b> добавлена в избранное!")
    # Планируем уведомления
    await callback.answer()