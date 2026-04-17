from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from datetime import datetime, timedelta
import pytz
from database import get_user, favorites
from utils import get_fixtures_by_team

scheduler = AsyncIOScheduler(timezone="UTC")

async def send_match_notification(bot: Bot, user_id, fixture, hours_before):
    user = get_user(user_id)
    if not user:
        return
    tz = pytz.timezone(user[4] or 'Asia/Almaty')
    match_time = datetime.fromisoformat(fixture['fixture']['date'][:-1]).replace(tzinfo=pytz.UTC).astimezone(tz)
    
    texts = {
        'ru': f"⚽ {fixture['teams']['home']['name']} — {fixture['teams']['away']['name']}\n"
              f"Время: {match_time.strftime('%H:%M')} (по вашему времени)\n"
              f"Лига: {fixture['league']['name']}",
        # kk и en можно добавить аналогично
    }
    
    await bot.send_message(user_id, texts.get(user[2], texts['ru']))
