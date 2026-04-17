from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import pytz
from aiogram import Bot
from database import get_user, get_favorites
from utils import get_fixtures

scheduler = AsyncIOScheduler(timezone="UTC")

async def send_match_notify(bot: Bot, user_id: int, fixture: dict, minutes_before: int):
    user = get_user(user_id)
    if not user: return
    tz = pytz.timezone(user[4] or "Asia/Almaty")
    match_utc = datetime.fromisoformat(fixture["fixture"]["date"][:-1])
    match_local = match_utc.replace(tzinfo=pytz.UTC).astimezone(tz)

    lang = user[2] or "ru"
    if lang == "ru":
        text = f"⚽ <b>{fixture['teams']['home']['name']} — {fixture['teams']['away']['name']}</b>\n\n" \
               f"🕒 Начало через <b>{minutes_before} мин</b> — {match_local.strftime('%H:%M')}\n" \
               f"🏟 {fixture['league']['name']}"
    elif lang == "kk":
        text = f"⚽ <b>{fixture['teams']['home']['name']} — {fixture['teams']['away']['name']}</b>\n\n" \
               f"🕒 {minutes_before} минуттан кейін"
    else:
        text = f"⚽ Match in <b>{minutes_before} min</b>: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}"

    await bot.send_message(user_id, text, parse_mode="HTML")

def schedule_all_notifications(bot: Bot):
    scheduler.start()
    print("🔔 Планировщик уведомлений запущен")