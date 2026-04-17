from datetime import datetime, timezone, timedelta, timezone
import pytz
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import ADMIN_ID, LANGUAGES, DEFAULT_TIMEZONE
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
    add_friend,
    get_friends,
    get_total_points,
    save_prediction,
    add_fixture,
    get_fixture_by_local_id,
    get_fixtures_by_team,
    get_all_upcoming_fixtures,
    update_fixture_score,
    delete_fixture,
    get_fixtures_in_range,
    get_last_fixtures_by_team,
    get_all_fixtures_count,
)
from keyboards import MENU_TEXTS, language_kb, main_menu, settings_kb_localized
from utils import get_city_timezone, is_top_match, normalize_lang, parse_utc_datetime, t, validate_timezone, fetch_fixtures_from_web

router = Router()


class UserState(StatesGroup):
    waiting_city = State()
    waiting_team_query = State()
    waiting_timezone = State()
    waiting_day_hour = State()
    waiting_before_minutes = State()
    waiting_quiet_range = State()
    waiting_broadcast = State()
    waiting_add_friend = State()
    waiting_fixture_score = State()


@router.message(Command("addfixture"))
async def cmd_add_fixture(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("en", "admin_denied"))
        return
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Используйте: /addfixture <Команда1 - Команда2 | Лига | ГГГГ-ММ-ДД ЧЧ:ММ | Статус | Счет (опционально)>\n"
            "Пример: /addfixture Chelsea - Real Madrid | Premier League | 2026-04-25 20:00 | scheduled | 2-1"
        )
        return
    data = args[1].strip()
    try:
        parts = [p.strip() for p in data.split("|")]
        if len(parts) < 4:
            raise ValueError("Требуется минимум 4 раздела, разделенных |")
        teams_part = parts[0]
        league = parts[1]
        datetime_part = parts[2]
        status = parts[3] if len(parts) > 3 else "scheduled"
        score_part = parts[4] if len(parts) > 4 else None

        if "-" not in teams_part:
            raise ValueError("Формат команд: Команда1 - Команда2")
        home_team, away_team = [t.strip() for t in teams_part.split("-", 1)]

        # Parse datetime with multiple formats
        try:
            match_date = datetime.strptime(datetime_part, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                match_date = datetime.fromisoformat(datetime_part.replace(" ", "T"))
            except ValueError:
                raise ValueError("Формат даты: ГГГГ-ММ-ДД ЧЧ:ММ")
        if match_date.tzinfo is None:
            match_date = match_date.replace(tzinfo=timezone.utc)

        score_home = None
        score_away = None
        if score_part and "-" in score_part:
            h, a = map(int, score_part.split("-", 1))
            score_home = h
            score_away = a

        fixture_id = add_fixture(
            home_team_name=home_team,
            away_team_name=away_team,
            league=league,
            match_date_utc=match_date.isoformat(),
            status=status,
            score_home=score_home,
            score_away=score_away,
            added_by=message.from_user.id,
        )
        await message.answer(f"Матч добавлен (ID: {fixture_id})")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(Command("setscore"))
async def cmd_set_score(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("en", "admin_denied"))
        return
    args = (message.text or "").split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /setscore <ID> <счет>\nПример: /setscore 5 2-1 или /setscore 5 FT")
        return
    try:
        fixture_id = int(args[1])
        score_text = args[2]
        fixture = get_fixture_by_local_id(fixture_id)
        if not fixture:
            await message.answer("Матч не найден")
            return
        if score_text.upper() in {"FT", "AET", "PEN", "NS", "LIVE"}:
            update_fixture_score(fixture_id, None, None, status=score_text.upper())
            await message.answer(f"Статус матча обновлен: {score_text}")
        else:
            if "-" not in score_text:
                await message.answer("Счет должен быть в формате 2-1")
                return
            h, a = map(int, score_text.split("-", 1))
            update_fixture_score(fixture_id, h, a, "finished")
            await message.answer(f"Счет обновлен: {h}-{a}")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@router.message(Command("matches"))
async def cmd_matches(message: Message):
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    timezone_name = user["timezone"] or DEFAULT_TIMEZONE
    tz = pytz.timezone(timezone_name)
    now_local = datetime.now(tz)

    favorites = get_favorites(message.from_user.id)
    if not favorites:
        await message.answer(t(lang, "teams_empty"))
        return

    lines = []
    for team_id, team_name in favorites:
        fixtures = get_fixtures_by_team(team_name, days=30)
        if fixtures:
            for fixture in fixtures:
                dt_utc = parse_utc_datetime(fixture["match_date_utc"])
                dt_local = dt_utc.astimezone(tz)
                score = ""
                if fixture["score_home"] is not None and fixture["score_away"] is not None:
                    score = f" ({fixture['score_home']}-{fixture['score_away']})"
                status = "🔴" if fixture["status"] == "live" else "✅" if fixture["status"] == "finished" else ""
                lines.append(
                    f"{status} {dt_local.strftime('%d.%m %H:%M')} - {fixture['home_team_name']} vs {fixture['away_team_name']}{score}\n"
                    f"🏆 {fixture['league']}"
                )

    all_fixtures = get_all_upcoming_fixtures(limit=10)
    if all_fixtures and not lines:
        await message.answer("Ближайшие матчи:")
        for fixture in all_fixtures[:10]:
            dt_utc = parse_utc_datetime(fixture["match_date_utc"])
            dt_local = dt_utc.astimezone(tz)
            lines.append(f"{dt_local.strftime('%d.%m %H:%M')} - {fixture['home_team_name']} vs {fixture['away_team_name']} ({fixture['league']})")

    if not lines:
        await message.answer("Матчей не найдено")
        return

    await message.answer("\n\n".join(lines[:15]))


@router.message(Command("allmatches"))
async def cmd_all_matches(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("en", "admin_denied"))
        return
    fixtures = get_all_upcoming_fixtures(limit=50)
    if not fixtures:
        await message.answer("Матчей нет")
        return
    lines = []
    for f in fixtures:
        dt = parse_utc_datetime(f["match_date_utc"]).strftime("%d.%m %H:%M")
        lines.append(f"ID{f['id']}: {dt} {f['home_team_name']} - {f['away_team_name']} ({f['league']}) [{f['status']}]")
    await message.answer("\n".join(lines[:30]))


@router.message(Command("scrape"))
async def cmd_scrape(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(t("en", "admin_denied"))
        return
    args = (message.text or "").split()
    if len(args) < 2:
        await message.answer("Использование: /scrape ГГГГ-ММ-ДД [дней]\nПример: /scrape 2026-04-18 3")
        return
    try:
        start_date_str = args[1]
        days = int(args[2]) if len(args) > 2 else 1
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    except Exception:
        await message.answer("Неверный формат даты. Используй ГГГГ-ММ-ДД")
        return

    added = 0
    for i in range(days):
        date_str = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        fixtures = await fetch_fixtures_from_web(date_str)
        for f in fixtures:
            # Avoid duplicates: check if same home/away/league at same datetime exists
            existing = get_all_upcoming_fixtures(limit=1000)
            # Simple dedup: compare home, away, time (within 1 hour)
            is_dup = False
            for ex in existing:
                if (ex["home_team_name"] == f["home_team_name"] and
                    ex["away_team_name"] == f["away_team_name"] and
                    abs((parse_utc_datetime(ex["match_date_utc"]) - parse_utc_datetime(f["match_date_utc"])).total_seconds()) < 3600):
                    is_dup = True
                    break
            if is_dup:
                continue
            add_fixture(
                home_team_name=f["home_team_name"],
                away_team_name=f["away_team_name"],
                league=f.get("league", "Unknown"),
                match_date_utc=f["match_date_utc"],
                status=f.get("status", "scheduled"),
                score_home=f.get("score_home"),
                score_away=f.get("score_away"),
            )
            added += 1
    await message.answer(f"Добавлено {added} матчей из веб-источника.")


def register_handlers(dp):
    dp.include_router(router)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    ensure_user(message.from_user.id, message.from_user.username)
    await message.answer(t("en", "welcome"), reply_markup=language_kb())


@router.message(Command("menu"))
async def cmd_menu(message: Message, state: FSMContext):
    await state.clear()
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))


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


@router.message(Command("apistatus"))
async def cmd_apistatus(message: Message):
    user = ensure_user(message.from_user.id, message.from_user.username)
    lang = normalize_lang(user["language"])
    if lang == "ru":
        text = "API-Football отключен (используется локальная база данных)."
    elif lang == "kk":
        text = "API-Football өшірілген (жергілікті дерекқор пайдаланылады)."
    else:
        text = "API-Football is disabled (using local database)."
    await message.answer(text)


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


@router.callback_query(F.data.startswith("del_"))
async def delete_team(callback: CallbackQuery):
    team_name = callback.data[4:]  # Extract team name after "del_"
    remove_favorite(callback.from_user.id, team_name)
    user = ensure_user(callback.from_user.id, callback.from_user.username)
    lang = normalize_lang(user["language"])
    await callback.message.answer(t(lang, "team_removed"))
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_team(callback: CallbackQuery):
    # Callback data format: add_{team_id}_{team_name} (legacy, team_id ignored)
    parts = callback.data.split("_", 2)
    if len(parts) >= 3:
        team_name = parts[2]
    else:
        team_name = parts[1] if len(parts) > 1 else ""
    if team_name:
        add_favorite(callback.from_user.id, team_name)
        user = ensure_user(callback.from_user.id, callback.from_user.username)
        lang = normalize_lang(user["language"])
        await callback.message.answer(t(lang, "team_added", team=team_name))
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
    elif action == "set_toggle_live_events":
        update_user(callback.from_user.id, live_events_enabled=0 if user["live_events_enabled"] else 1)
    elif action.startswith("set_profile_"):
        update_user(callback.from_user.id, notify_profile=action.replace("set_profile_", ""))
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
    menu = MENU_TEXTS.get(lang, MENU_TEXTS["en"])
    text = (message.text or "").strip()

    # Allow leaving timezone input mode using menu buttons.
    if text in {
        menu["teams"],
        menu["add"],
        menu["today"],
        menu["next5"],
        menu["center"],
        menu["weekend"],
        menu["fantasy"],
        menu["league"],
        menu["settings"],
    }:
        await state.clear()
        await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
        return

    timezone_name = text
    if not validate_timezone(timezone_name):
        await message.answer(t(lang, "invalid_timezone"))
        return
    update_user(message.from_user.id, timezone=timezone_name)
    await message.answer(t(lang, "timezone_saved", timezone=timezone_name))
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
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
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
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
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
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
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
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
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
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
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
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

    if query in {menu["teams"], menu["today"], menu["next5"], menu["center"], menu["weekend"], menu["fantasy"], menu["league"], menu["settings"]}:
        await state.clear()
        await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
        return

    # Добавляем команду напрямую по названию
    add_favorite(message.from_user.id, query)
    await message.answer(t(lang, "team_added", team=query))
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))
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
                [InlineKeyboardButton(text=f"❌ {name}", callback_data=f"del_{name}")]
                for name in favorites
            ]
        )
        body = "\n".join([f"• {name}" for name in favorites])
        await message.answer(body, reply_markup=kb)
        return

    if text == menu["today"]:
        favorites = get_favorites(message.from_user.id)
        if not favorites:
            await message.answer(t(lang, "teams_empty"))
            return
        timezone_name = user["timezone"]
        tz = pytz.timezone(timezone_name)
        now_local = datetime.now(tz)
        rows = []
        for team_name in favorites:
            fixtures = get_fixtures_by_team(team_name, days=1)
            for fixture in fixtures:
                dt_utc = parse_utc_datetime(fixture["match_date_utc"])
                dt_local = dt_utc.astimezone(tz)
                if dt_local.date() != now_local.date():
                    continue
                rows.append(
                    f"{dt_local.strftime('%H:%M')} - {fixture['home_team_name']} vs {fixture['away_team_name']}"
                )
        if not rows:
            await message.answer(t(lang, "today_empty"))
            return
        uniq_rows = sorted(set(rows))
        await message.answer(t(lang, "today_title") + "\n" + "\n".join(uniq_rows[:25]))
        return
        timezone_name = user["timezone"]
        tz = pytz.timezone(timezone_name)
        now_local = datetime.now(tz)
        rows = []
        for team_name in favorites:
            fixtures = get_fixtures_by_team(team_name, days=1)
            for fixture in fixtures:
                dt_utc = parse_utc_datetime(fixture["match_date_utc"])
                dt_local = dt_utc.astimezone(tz)
                if dt_local.date() != now_local.date():
                    continue
                rows.append(
                    f"{dt_local.strftime('%H:%M')} - {fixture['home_team_name']} vs {fixture['away_team_name']}"
                )
        if not rows:
            await message.answer(t(lang, "today_empty"))
            return
        uniq_rows = sorted(set(rows))
        await message.answer(t(lang, "today_title") + "\n" + "\n".join(uniq_rows[:25]))
        return

    if text == menu["center"]:
        favorites = get_favorites(message.from_user.id)
        if not favorites:
            await message.answer(t(lang, "teams_empty"))
            return
        timezone_name = user["timezone"]
        tz = pytz.timezone(timezone_name)
        now_local = datetime.now(tz)
        cards = []
        for team_name in favorites:
            fixtures = get_fixtures_by_team(team_name, days=2)
            for fixture in fixtures:
                dt_utc = parse_utc_datetime(fixture["match_date_utc"])
                dt_local = dt_utc.astimezone(tz)
                if dt_local < now_local:
                    continue
                home_name = fixture["home_team_name"]
                away_name = fixture["away_team_name"]
                venue = fixture.get("round", "N/A")
                referee = "N/A"
                countdown = int((dt_local - now_local).total_seconds() // 60)
                h2h = "N/A"
                home_form = "N/A"
                away_form = "N/A"
                text_card = (
                    f"⚽ <b>{home_name} vs {away_name}</b>\n"
                    f"🕒 {dt_local.strftime('%d.%m %H:%M')} ({timezone_name})\n"
                    f"⏳ Через: {countdown} мин\n"
                    f"🏟 Стадион: {venue}\n"
                    f"🧑‍⚖️ Судья: {referee}\n"
                    f"🌤 Погода: N/A\n"
                    f"📊 H2H: {h2h}\n"
                    f"📈 Form: {home_form} vs {away_form}\n"
                    f"🔥 {'Топ-матч/дерби' if is_top_match(fixture) else 'Обычный матч'}"
                )
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=t(lang, "score_reveal"), callback_data=f"score_{fixture['id']}")],
                        [
                            InlineKeyboardButton(text="1", callback_data=f"pred_{fixture['id']}_1"),
                            InlineKeyboardButton(text="X", callback_data=f"pred_{fixture['id']}_x"),
                            InlineKeyboardButton(text="2", callback_data=f"pred_{fixture['id']}_2"),
                        ],
                    ]
                )
                cards.append((dt_local, text_card, kb))
        if not cards:
            await message.answer(t(lang, "today_empty"))
            return
        await message.answer(t(lang, "match_center_title"))
        for _, text_card, kb in sorted(cards, key=lambda x: x[0])[:8]:
            await message.answer(text_card, reply_markup=kb)
        return

    if text == menu["next5"]:
        favorites = get_favorites(message.from_user.id)
        if not favorites:
            await message.answer(t(lang, "teams_empty"))
            return
        timezone_name = user["timezone"]
        tz = pytz.timezone(timezone_name)
        now_local = datetime.now(tz)
        upcoming = []
        seen_fixture_ids = set()

        for team_name in favorites:
            fixtures = get_fixtures_by_team(team_name, days=60)
            for fixture in fixtures:
                fixture_id = fixture["id"]
                if fixture_id in seen_fixture_ids:
                    continue
                dt_utc = parse_utc_datetime(fixture["match_date_utc"])
                dt_local = dt_utc.astimezone(tz)
                if dt_local <= now_local:
                    continue
                seen_fixture_ids.add(fixture_id)
                upcoming.append(
                    {
                        "dt": dt_local,
                        "home": fixture["home_team_name"],
                        "away": fixture["away_team_name"],
                        "league": fixture["league"],
                        "team_name": team_name,
                    }
                )

        if not upcoming:
            played = []
            seen_last_ids = set()
            for team_name in favorites:
                fixtures = get_last_fixtures_by_team(team_name, count=8)
                for fixture in fixtures:
                    fixture_id = fixture["id"]
                    if fixture_id in seen_last_ids:
                        continue
                    dt_utc = parse_utc_datetime(fixture["match_date_utc"])
                    dt_local = dt_utc.astimezone(tz)
                    seen_last_ids.add(fixture_id)
                    hg = fixture["score_home"]
                    ag = fixture["score_away"]
                    score_info = f"{hg}-{ag}" if hg is not None and ag is not None else "N/A"
                    played.append(
                        {
                            "dt": dt_local,
                            "home": fixture["home_team_name"],
                            "away": fixture["away_team_name"],
                            "league": fixture["league"],
                            "team_name": team_name,
                            "score": score_info,
                        }
                    )
            if not played:
                await message.answer(t(lang, "next5_empty") + "\nПопробуй добавить еще команду или проверь межсезонье.")
                return
            last5 = sorted(played, key=lambda row: row["dt"], reverse=True)[:5]
            lines = []
            for row in last5:
                lines.append(
                    f"{row['dt'].strftime('%d.%m %H:%M')} - {row['home']} vs {row['away']} ({row['score']})\n"
                    f"🏆 {row['league']} | ⭐ {row['team_name']}"
                )
            await message.answer(t(lang, "next5_last_title") + "\n\n" + "\n\n".join(lines))
            return

        top5 = sorted(upcoming, key=lambda row: row["dt"])[:5]
        lines = []
        for row in top5:
            lines.append(
                f"{row['dt'].strftime('%d.%m %H:%M')} - {row['home']} vs {row['away']}\n"
                f"🏆 {row['league']} | ⭐ {row['team_name']}"
            )
        await message.answer(t(lang, "next5_title") + "\n\n" + "\n\n".join(lines))
        return

    if text == menu["weekend"]:
        favorites = get_favorites(message.from_user.id)
        if not favorites:
            await message.answer(t(lang, "teams_empty"))
            return
        timezone_name = user["timezone"]
        tz = pytz.timezone(timezone_name)
        now_local = datetime.now(tz)
        picks = []
        for team_name in favorites:
            fixtures = get_fixtures_by_team(team_name, days=7)
            for fixture in fixtures:
                dt_utc = parse_utc_datetime(fixture["match_date_utc"])
                dt_local = dt_utc.astimezone(tz)
                if dt_local.weekday() not in (5, 6):
                    continue
                if dt_local <= now_local:
                    continue
                picks.append((dt_local, fixture, team_name))
        if not picks:
            await message.answer(t(lang, "next5_empty"))
            return
        lines = []
        for dt_local, fixture, team_name in sorted(picks, key=lambda x: x[0])[:8]:
            hot = "🔥" if is_top_match(fixture) else "•"
            lines.append(f"{hot} {dt_local.strftime('%a %H:%M')} {fixture['home_team_name']} vs {fixture['away_team_name']} ({team_name})")
        await message.answer(t(lang, "weekend_title") + "\n" + "\n".join(lines))
        return

    if text == menu["fantasy"]:
        await message.answer("Фэнтези-помощник временно недоступен (требуются данные из API).")
        return

    is_league_click = (
        text == menu["league"]
        or "мини-лига" in text.lower()
        or "мини лига" in text.lower()
        or "mini league" in text.lower()
        or "мини-лига" in text.lower()
    )
    if is_league_click:
        friends = get_friends(message.from_user.id)
        members = [message.from_user.id] + friends
        board = []
        for uid in members:
            points = get_total_points(uid)
            board.append((points, uid))
        board.sort(reverse=True)
        lines = [f"{idx+1}. {uid} - {pts} pts" for idx, (pts, uid) in enumerate(board[:10])]
        lines.append("\nДобавить друга: /addfriend <user_id>")
        await message.answer(t(lang, "league_title") + "\n" + "\n".join(lines))
        return

    if text == menu["settings"]:
        refreshed = get_user(message.from_user.id)
        await message.answer(
            t(lang, "settings_title"),
            reply_markup=settings_kb_localized(refreshed, lang),
        )
        return

    # Если текст не является командой меню — добавляем команду
    add_favorite(message.from_user.id, None, text)
    await message.answer(t(lang, "team_added", team=text))
    await message.answer(t(lang, "main_hint"), reply_markup=main_menu(lang))


@router.callback_query(F.data.startswith("score_"))
async def reveal_score(callback: CallbackQuery):
    fixture_id = int(callback.data.split("_", 1)[1])
    fixture = get_fixture_by_local_id(fixture_id)
    if not fixture:
        await callback.answer("Матч не найден", show_alert=True)
        return
    home = fixture["home_team_name"]
    away = fixture["away_team_name"]
    hg = fixture["score_home"]
    ag = fixture["score_away"]
    status = fixture["status"]
    score_text = f"{hg}-{ag}" if hg is not None and ag is not None else "N/A"
    await callback.message.answer(f"📊 <b>{home} {score_text} {away}</b>\nСтатус: {status}")
    await callback.answer()


@router.callback_query(F.data.startswith("pred_"))
async def save_prediction_callback(callback: CallbackQuery):
    _, fixture_id, pred = callback.data.split("_", 2)
    save_prediction(callback.from_user.id, int(fixture_id), pred.upper())
    await callback.answer("Прогноз сохранен!")


@router.message(Command("addfriend"))
async def cmd_addfriend(message: Message):
    args = (message.text or "").split()
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Использование: /addfriend <user_id>")
        return
    friend_id = int(args[1])
    add_friend(message.from_user.id, friend_id)
    await message.answer(f"Друг {friend_id} добавлен в мини-лигу.")