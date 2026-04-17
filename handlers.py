from datetime import datetime
import pytz
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import ADMIN_ID, LANGUAGES
from database import (
    add_favorite,
    ensure_user,
    get_favorites,
    get_favorites_count,
    get_user,
    get_users_count,
    get_all_users,
    remove_favorite,
    update_user,
)
from keyboards import MENU_TEXTS, language_kb, main_menu, settings_kb_localized
from utils import get_city_timezone, get_fixtures, normalize_lang, search_teams, t, validate_timezone
from utils import get_team_form, parse_utc_datetime

router = Router()


class UserState(StatesGroup):
    waiting_city = State()
    waiting_team_query = State()
    waiting_timezone = State()
    waiting_day_hour = State()
    waiting_before_minutes = State()
    waiting_quiet_range = State()
    waiting_broadcast = State()


def register_handlers(dp):
    dp.include_router(router)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    ensure_user(message.from_user.id, message.from_user.username)
    await message.answer(t("en", "welcome"), reply_markup=language_kb())


@router.callback_query(F.data.startswith("lang_"))
async def choose_lang(callback: CallbackQuery, state: FSMContext):
    lang = callback.data[5:]
    ensure_user(callback.from_user.id, callback.from_user.username)
    if lang not in LANGUAGES:
        lang = "en"
    update_user(callback.from_user.id, language=lang)
    await callback.message.edit_text(f"✅ {LANGUAGES[lang]}")
    await callback.message.answer(t(lang, "ask_city"))
    await state.set_state(UserState.waiting_city)
    await callback.answer()


@router.message(UserState.waiting_city)
async def save_city(message: Message, state: FSMContext):
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    city = (message.text or "").strip()
    timezone_name = await get_city_timezone(city)
    update_user(message.from_user.id, city=city, timezone=timezone_name)
    await message.answer(
        t(lang, "city_saved", city=city, timezone=timezone_name),
        reply_markup=main_menu(lang),
    )
    await message.answer(t(lang, "main_hint"))
    await state.clear()


@router.message(Command("admin"))
async def admin_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("en", "admin_denied"))
        return
    await message.answer(
        t("ru", "admin_stats", users=get_users_count(), favorites=get_favorites_count())
    )


@router.message(Command("broadcast"))
async def admin_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("en", "admin_denied"))
        return
    await state.set_state(UserState.waiting_broadcast)
    await message.answer(t("ru", "broadcast_hint"))


@router.message(UserState.waiting_broadcast)
async def do_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await state.clear()
        return
    payload = message.text or ""
    users = get_all_users()
    sent = 0
    for user in users:
        try:
            await message.bot.send_message(user["user_id"], payload, parse_mode="HTML")
            sent += 1
        except Exception:
            continue
    await message.answer(t("ru", "broadcast_done", sent=sent, total=len(users)))
    await state.clear()


@router.callback_query(F.data.startswith("add_"))
async def add_team(callback: CallbackQuery):
    _, team_id, team_name = callback.data.split("_", 2)
    add_favorite(callback.from_user.id, int(team_id), team_name)
    user = ensure_user(callback.from_user.id, callback.from_user.username)
    lang = normalize_lang(user["language"])
    await callback.message.answer(t(lang, "team_added", team=team_name))
    await callback.answer()


@router.callback_query(F.data.startswith("del_"))
async def delete_team(callback: CallbackQuery):
    _, team_id = callback.data.split("_", 1)
    remove_favorite(callback.from_user.id, int(team_id))
    user = ensure_user(callback.from_user.id, callback.from_user.username)
    lang = normalize_lang(user["language"])
    await callback.message.answer(t(lang, "team_removed"))
    await callback.answer()


@router.callback_query(F.data.startswith("set_"))
async def settings_callback(callback: CallbackQuery, state: FSMContext):
    user = ensure_user(callback.from_user.id, callback.from_user.username)
    lang = normalize_lang(user["language"])
    action = callback.data
    if action == "set_toggle_day":
        update_user(callback.from_user.id, notify_day_enabled=0 if user["notify_day_enabled"] else 1)
    elif action == "set_toggle_before":
        update_user(callback.from_user.id, notify_before_enabled=0 if user["notify_before_enabled"] else 1)
    elif action == "set_toggle_lineup":
        update_user(callback.from_user.id, notify_lineup_enabled=0 if user["notify_lineup_enabled"] else 1)
    elif action == "set_toggle_quiet":
        update_user(callback.from_user.id, quiet_hours_enabled=0 if user["quiet_hours_enabled"] else 1)
    elif action == "set_day_hour":
        await state.set_state(UserState.waiting_day_hour)
        prompts = {
            "ru": "Отправь час для дневного уведомления (0-23)",
            "kk": "Күндізгі хабарлама уақытын жібер (0-23)",
            "en": "Send day notification hour (0-23)",
        }
        await callback.message.answer(prompts.get(lang, prompts["en"]))
        await callback.answer()
        return
    elif action == "set_before_minutes":
        await state.set_state(UserState.waiting_before_minutes)
        prompts = {
            "ru": "Отправь минуты до матча (10-720)",
            "kk": "Матчқа дейінгі минутты жібер (10-720)",
            "en": "Send before-match minutes (10-720)",
        }
        await callback.message.answer(prompts.get(lang, prompts["en"]))
        await callback.answer()
        return
    elif action == "set_quiet_range":
        await state.set_state(UserState.waiting_quiet_range)
        prompts = {
            "ru": "Отправь тихий диапазон как ЧЧ-ЧЧ (пример: 23-8)",
            "kk": "Тыныш уақытты СС-СС форматында жібер (мысалы: 23-8)",
            "en": "Send quiet range as HH-HH (example: 23-8)",
        }
        await callback.message.answer(prompts.get(lang, prompts["en"]))
        await callback.answer()
        return
    elif action == "set_timezone":
        await state.set_state(UserState.waiting_timezone)
        await callback.message.answer(t(lang, "ask_timezone"))
        await callback.answer()
        return

    updated_user = get_user(callback.from_user.id)
    await callback.message.edit_text(
        t(lang, "settings_title"),
        reply_markup=settings_kb_localized(updated_user, lang),
    )
    await callback.answer(t(lang, "settings_saved"))


@router.message(UserState.waiting_timezone)
async def set_timezone_handler(message: Message, state: FSMContext):
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    timezone_name = (message.text or "").strip()
    if not validate_timezone(timezone_name):
        await message.answer(t(lang, "invalid_timezone"))
        return
    update_user(message.from_user.id, timezone=timezone_name)
    await message.answer(t(lang, "timezone_saved", timezone=timezone_name))
    await state.clear()


@router.message(UserState.waiting_day_hour)
async def set_day_hour_handler(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not value.isdigit() or not 0 <= int(value) <= 23:
        texts = {
            "ru": "Час должен быть от 0 до 23.",
            "kk": "Сағат 0 мен 23 аралығында болуы керек.",
            "en": "Hour should be from 0 to 23.",
        }
        user = ensure_user(message.from_user.id, message.from_user.username)
        lang = normalize_lang(user["language"])
        await message.answer(texts.get(lang, texts["en"]))
        return
    update_user(message.from_user.id, notify_day_hour=int(value))
    texts = {
        "ru": "Час дневного уведомления обновлен.",
        "kk": "Күндізгі хабарлама уақыты жаңартылды.",
        "en": "Day notification hour updated.",
    }
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    await message.answer(texts.get(lang, texts["en"]))
    await state.clear()


@router.message(UserState.waiting_before_minutes)
async def set_before_minutes_handler(message: Message, state: FSMContext):
    value = (message.text or "").strip()
    if not value.isdigit() or not 10 <= int(value) <= 720:
        texts = {
            "ru": "Минуты должны быть от 10 до 720.",
            "kk": "Минут 10 бен 720 аралығында болуы керек.",
            "en": "Minutes should be from 10 to 720.",
        }
        user = ensure_user(message.from_user.id, message.from_user.username)
        lang = normalize_lang(user["language"])
        await message.answer(texts.get(lang, texts["en"]))
        return
    update_user(message.from_user.id, notify_before_minutes=int(value))
    texts = {
        "ru": "Напоминание перед матчем обновлено.",
        "kk": "Матч алдындағы еске салғыш жаңартылды.",
        "en": "Before-match reminder updated.",
    }
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    await message.answer(texts.get(lang, texts["en"]))
    await state.clear()


@router.message(UserState.waiting_quiet_range)
async def set_quiet_range_handler(message: Message, state: FSMContext):
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    value = (message.text or "").strip().replace(" ", "")
    if "-" not in value:
        texts = {
            "ru": "Формат должен быть ЧЧ-ЧЧ (пример: 23-8).",
            "kk": "Формат СС-СС болуы керек (мысалы: 23-8).",
            "en": "Format should be HH-HH (example: 23-8).",
        }
        await message.answer(texts.get(lang, texts["en"]))
        return
    left, right = value.split("-", 1)
    if not left.isdigit() or not right.isdigit():
        texts = {
            "ru": "Используй только цифры, пример: 23-8.",
            "kk": "Тек сандарды қолдан, мысалы: 23-8.",
            "en": "Use numbers only, example: 23-8.",
        }
        await message.answer(texts.get(lang, texts["en"]))
        return
    start = int(left)
    end = int(right)
    if not (0 <= start <= 23 and 0 <= end <= 23):
        texts = {
            "ru": "Часы должны быть в диапазоне 0..23.",
            "kk": "Сағат 0..23 диапазонында болуы керек.",
            "en": "Hours must be in range 0..23.",
        }
        await message.answer(texts.get(lang, texts["en"]))
        return
    update_user(message.from_user.id, quiet_start_hour=start, quiet_end_hour=end)
    await message.answer(t(lang, "quiet_saved", start=start, end=end))
    await state.clear()


@router.message(UserState.waiting_team_query)
async def team_search_from_state(message: Message, state: FSMContext):
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    menu = MENU_TEXTS.get(lang, MENU_TEXTS["en"])
    query = (message.text or "").strip()

    if query == menu["add"]:
        await message.answer(t(lang, "ask_team_query"))
        return

    if query in {menu["teams"], menu["today"], menu["settings"]}:
        await state.clear()
        await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
        return

    teams = await search_teams(query)
    if not teams:
        await message.answer(t(lang, "search_empty"))
        return
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=team["team"]["name"],
                    callback_data=f"add_{team['team']['id']}_{team['team']['name']}",
                )
            ]
            for team in teams
        ]
    )
    await message.answer(t(lang, "select_team"), reply_markup=kb)
    await state.clear()


@router.message()
async def main_handler(message: Message, state: FSMContext):
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])

    if not user["city"] or not user["timezone"]:
        await message.answer(t(lang, "ask_city"))
        await state.set_state(UserState.waiting_city)
        return

    menu = MENU_TEXTS.get(lang, MENU_TEXTS["en"])
    text = (message.text or "").strip()

    if text == menu["add"]:
        await message.answer(t(lang, "ask_team_query"))
        await state.set_state(UserState.waiting_team_query)
        return

    if text == menu["teams"]:
        favorites = get_favorites(message.from_user.id)
        if not favorites:
            await message.answer(t(lang, "teams_empty"))
            return
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"❌ {name}", callback_data=f"del_{team_id}")]
                for team_id, name in favorites
            ]
        )
        body = "\n".join([f"• {name}" for _, name in favorites])
        await message.answer(body, reply_markup=kb)
        return

    if text == menu["today"]:
        favorites = get_favorites(message.from_user.id)
        if not favorites:
            await message.answer(t(lang, "teams_empty"))
            return
        timezone_name = user["timezone"]
        now_local = datetime.now(pytz.timezone(timezone_name))
        rows = []
        for team_id, _ in favorites:
            fixtures = await get_fixtures(int(team_id), days=1)
            for fixture in fixtures:
                dt_utc = parse_utc_datetime(fixture["fixture"]["date"])
                dt_local = dt_utc.astimezone(pytz.timezone(timezone_name))
                if dt_local.date() != now_local.date():
                    continue
                team_form = await get_team_form(int(team_id))
                rows.append(
                    f"{dt_local.strftime('%H:%M')} - {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']} | form: {team_form}"
                )
        if not rows:
            await message.answer(t(lang, "today_empty"))
            return
        uniq_rows = sorted(set(rows))
        await message.answer(t(lang, "today_title") + "\n" + "\n".join(uniq_rows[:25]))
        return

    if text == menu["settings"]:
        refreshed = get_user(message.from_user.id)
        await message.answer(
            t(lang, "settings_title"),
            reply_markup=settings_kb_localized(refreshed, lang),
        )
        return

    teams = await search_teams(text)
    if teams:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=team["team"]["name"],
                        callback_data=f"add_{team['team']['id']}_{team['team']['name']}",
                    )
                ]
                for team in teams
            ]
        )
        await message.answer(t(lang, "select_team"), reply_markup=kb)
    else:
        await message.answer(t(lang, "main_hint"))