from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
import pytz
from aiogram import Bot
from database import (
    get_all_users,
    get_favorites,
    get_fixture_snapshot,
    mark_notification_sent,
    set_fixture_snapshot,
    was_notification_sent,
)
from utils import get_fixtures, parse_utc_datetime, t, utc_to_user_local
from config import DEFAULT_TIMEZONE

scheduler = AsyncIOScheduler(timezone="UTC")


def _tz_shortname(tz_name: str) -> str:
    try:
        return pytz.timezone(tz_name).localize(datetime.now()).tzname() or tz_name
    except Exception:
        return tz_name


def _in_quiet_hours(user, now_local: datetime) -> bool:
    if not user["quiet_hours_enabled"]:
        return False
    start_hour = int(user["quiet_start_hour"])
    end_hour = int(user["quiet_end_hour"])
    hour = now_local.hour
    if start_hour == end_hour:
        return True
    if start_hour < end_hour:
        return start_hour <= hour < end_hour
    return hour >= start_hour or hour < end_hour


async def _process_fixture(bot: Bot, user, fixture: dict) -> None:
    fixture_id = int(fixture["fixture"]["id"])
    starts_at = fixture["fixture"]["date"]
    home = fixture["teams"]["home"]["name"]
    away = fixture["teams"]["away"]["name"]
    league = fixture["league"]["name"]
    tz_name = user["timezone"] or DEFAULT_TIMEZONE
    lang = user["language"] or "en"

    dt_utc = parse_utc_datetime(starts_at)
    dt_local = utc_to_user_local(dt_utc, tz_name)
    now_local = datetime.now(pytz.timezone(tz_name))
    if _in_quiet_hours(user, now_local):
        return
    mins_left = int((dt_local - now_local).total_seconds() // 60)
    tz_label = _tz_shortname(tz_name)

    old_snapshot = get_fixture_snapshot(user["user_id"], fixture_id)
    if old_snapshot and old_snapshot != starts_at and not was_notification_sent(
        user["user_id"], fixture_id, "time_changed"
    ):
        await bot.send_message(
            user["user_id"],
            t(
                lang,
                "time_changed",
                home=home,
                away=away,
                time=dt_local.strftime("%H:%M"),
                tz=tz_label,
            ),
            parse_mode="HTML",
        )
        mark_notification_sent(user["user_id"], fixture_id, "time_changed")
    set_fixture_snapshot(user["user_id"], fixture_id, starts_at)

    if user["notify_day_enabled"] and dt_local.date() == now_local.date():
        day_key = f"day_{now_local.date().isoformat()}"
        if now_local.hour >= int(user["notify_day_hour"]) and not was_notification_sent(
            user["user_id"], fixture_id, day_key
        ):
            await bot.send_message(
                user["user_id"],
                t(
                    lang,
                    "match_day",
                    home=home,
                    away=away,
                    time=dt_local.strftime("%H:%M"),
                    tz=tz_label,
                    league=league,
                ),
                parse_mode="HTML",
            )
            mark_notification_sent(user["user_id"], fixture_id, day_key)

    before_minutes = int(user["notify_before_minutes"])
    if user["notify_before_enabled"] and 0 <= mins_left <= before_minutes:
        before_key = f"before_{before_minutes}"
        if not was_notification_sent(user["user_id"], fixture_id, before_key):
            await bot.send_message(
                user["user_id"],
                t(
                    lang,
                    "match_before",
                    home=home,
                    away=away,
                    time=dt_local.strftime("%H:%M"),
                    tz=tz_label,
                    minutes=mins_left,
                ),
                parse_mode="HTML",
            )
            mark_notification_sent(user["user_id"], fixture_id, before_key)

    if user["notify_lineup_enabled"] and 0 <= mins_left <= 60:
        if not was_notification_sent(user["user_id"], fixture_id, "lineup_60"):
            await bot.send_message(
                user["user_id"],
                t(lang, "lineup_soon", home=home, away=away),
                parse_mode="HTML",
            )
            mark_notification_sent(user["user_id"], fixture_id, "lineup_60")


async def notifications_job(bot: Bot) -> None:
    users = get_all_users()
    for user in users:
        favorites = get_favorites(user["user_id"])
        if not favorites:
            continue
        for team_id, _ in favorites:
            fixtures = await get_fixtures(int(team_id), days=3)
            for fixture in fixtures:
                fixture_date = parse_utc_datetime(fixture["fixture"]["date"])
                if fixture_date < datetime.now(timezone.utc) - timedelta(minutes=10):
                    continue
                await _process_fixture(bot, user, fixture)


def schedule_all_notifications(bot: Bot):
    if not scheduler.running:
        scheduler.start()
    scheduler.add_job(
        notifications_job,
        "interval",
        minutes=5,
        args=[bot],
        id="notifications_job",
        replace_existing=True,
        max_instances=1,
    )
    print("Scheduler started: notifications every 5 minutes")