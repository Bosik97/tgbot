import aiohttp
from datetime import datetime, timedelta, timezone
import asyncio
from geopy.geocoders import Nominatim
import pytz
from config import API_FOOTBALL_KEY, API_BASE_URL, DEFAULT_TIMEZONE, I18N

headers = {"x-apisports-key": API_FOOTBALL_KEY}
_api_cache = {}
_api_lock = asyncio.Semaphore(4)
CITY_TZ_OVERRIDES = {
    "almaty": "Asia/Almaty",
    "astana": "Asia/Almaty",
    "moscow": "Europe/Moscow",
    "saint petersburg": "Europe/Moscow",
    "spb": "Europe/Moscow",
    "shymkent": "Asia/Almaty",
    "aktobe": "Asia/Aqtobe",
    "atyrau": "Asia/Atyrau",
    "karaganda": "Asia/Almaty",
}


def t(lang: str, key: str, **kwargs) -> str:
    pack = I18N.get(lang, I18N["en"])
    template = pack.get(key, I18N["en"].get(key, key))
    return template.format(**kwargs)


def normalize_lang(lang: str) -> str:
    return lang if lang in I18N else "en"


def parse_utc_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def utc_to_user_local(dt_utc: datetime, timezone_name: str) -> datetime:
    tz = pytz.timezone(timezone_name or DEFAULT_TIMEZONE)
    return dt_utc.astimezone(tz)


def validate_timezone(timezone_name: str) -> bool:
    return timezone_name in pytz.all_timezones_set


async def search_teams(query: str):
    payload = await _api_get(f"{API_BASE_URL}/teams?search={query}", ttl_seconds=600)
    return payload.get("response", [])[:8]


async def get_fixtures(team_id: int, days: int = 14):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    until = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"{API_BASE_URL}/fixtures?team={team_id}&from={today}&to={until}"
    payload = await _api_get(url, ttl_seconds=90)
    return payload.get("response", [])


async def get_team_form(team_id: int, last: int = 5) -> str:
    url = f"{API_BASE_URL}/fixtures?team={team_id}&last={last}"
    payload = await _api_get(url, ttl_seconds=3600)
    fixtures = payload.get("response", [])
    form = []
    for fixture in fixtures:
        home_id = fixture["teams"]["home"]["id"]
        away_id = fixture["teams"]["away"]["id"]
        home_goals = fixture["goals"]["home"]
        away_goals = fixture["goals"]["away"]
        if home_goals is None or away_goals is None:
            continue
        if team_id == home_id:
            form.append("W" if home_goals > away_goals else "D" if home_goals == away_goals else "L")
        elif team_id == away_id:
            form.append("W" if away_goals > home_goals else "D" if away_goals == home_goals else "L")
    return "".join(form) if form else "N/A"


async def get_city_timezone(city: str):
    try:
        key = city.strip().lower()
        if key in CITY_TZ_OVERRIDES:
            return CITY_TZ_OVERRIDES[key]
        geo = Nominatim(user_agent="football_bot")
        loc = geo.geocode(city)
        if loc:
            country_tzs = pytz.country_timezones.get(
                loc.raw.get("country_code", "KZ").upper(),
                [DEFAULT_TIMEZONE],
            )
            return country_tzs[0] if country_tzs else DEFAULT_TIMEZONE
    except Exception:
        pass
    return DEFAULT_TIMEZONE


async def _api_get(url: str, ttl_seconds: int = 120) -> dict:
    now = datetime.now(timezone.utc)
    cached = _api_cache.get(url)
    if cached and cached["expires_at"] > now:
        return cached["payload"]

    async with _api_lock:
        # Re-check after waiting the semaphore.
        cached = _api_cache.get(url)
        if cached and cached["expires_at"] > now:
            return cached["payload"]
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as resp:
                payload = await resp.json()
                _api_cache[url] = {
                    "expires_at": now + timedelta(seconds=ttl_seconds),
                    "payload": payload,
                }
                return payload