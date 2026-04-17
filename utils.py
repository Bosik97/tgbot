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
CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "і": "i", "ң": "n", "ғ": "g", "ү": "u", "ұ": "u", "қ": "k", "ө": "o", "һ": "h",
}
TEAM_QUERY_ALIASES = {
    "челси": "chelsea",
    "ман сити": "manchester city",
    "манчестер сити": "manchester city",
    "ман юнайтед": "manchester united",
    "манчестер юнайтед": "manchester united",
    "ливерпуль": "liverpool",
    "арсенал": "arsenal",
    "тоттенхэм": "tottenham",
    "барселона": "barcelona",
    "реал": "real madrid",
    "реал мадрид": "real madrid",
    "атлетико": "atletico madrid",
    "бавария": "bayern munich",
    "псж": "paris saint germain",
    "интер": "inter",
    "милан": "milan",
    "ювентус": "juventus",
    "ростов": "fc rostov",
    "зенит": "zenit",
    "спартак": "spartak moscow",
    "цска": "cska moscow",
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
    query = query.strip()
    if not query:
        return []

    results = await _search_teams_raw(query)

    alias_query = TEAM_QUERY_ALIASES.get(query.lower())
    if alias_query:
        alias_results = await _search_teams_raw(alias_query)
        results = _merge_team_results(results, alias_results)

    if _looks_cyrillic(query):
        translit_query = translit_cyrillic_to_latin(query)
        if translit_query and translit_query.lower() != query.lower():
            fallback_results = await _search_teams_raw(translit_query)
            results = _merge_team_results(results, fallback_results)

    return results[:8]


async def get_fixtures(team_id: int, days: int = 14):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    until = (datetime.now(timezone.utc) + timedelta(days=days)).strftime("%Y-%m-%d")
    url = f"{API_BASE_URL}/fixtures?team={team_id}&from={today}&to={until}"
    payload = await _api_get(url, ttl_seconds=90)
    return payload.get("response", [])


async def get_next_fixtures(team_id: int, count: int = 5):
    payload = await _api_get(f"{API_BASE_URL}/fixtures?team={team_id}&next={count}", ttl_seconds=90)
    return payload.get("response", [])


async def get_last_fixtures(team_id: int, count: int = 5):
    payload = await _api_get(f"{API_BASE_URL}/fixtures?team={team_id}&last={count}", ttl_seconds=300)
    return payload.get("response", [])


async def get_upcoming_fixtures(team_id: int, limit: int = 10):
    """
    Robust upcoming fixtures fetch with multi-step fallback.
    Returns tuple: (fixtures, diagnostic_message_or_empty)
    """
    diagnostics = []
    now_utc = datetime.now(timezone.utc)

    # Free plan friendly strategy:
    # - Avoid `next` parameter
    # - Query only allowed seasons, then filter upcoming locally.
    # Default free-plan season window is typically 2022..2024.
    candidate_seasons = [2024, 2023, 2022]
    all_upcoming = []

    for season in candidate_seasons:
        payload = await _api_get(
            f"{API_BASE_URL}/fixtures?team={team_id}&season={season}",
            ttl_seconds=600,
        )
        fixtures = payload.get("response", [])
        if fixtures:
            for fixture in fixtures:
                date_raw = fixture.get("fixture", {}).get("date")
                if not date_raw:
                    continue
                try:
                    dt_utc = parse_utc_datetime(date_raw)
                except Exception:
                    continue
                if dt_utc > now_utc:
                    all_upcoming.append(fixture)
        else:
            err = _extract_api_errors(payload)
            if err:
                diagnostics.append(f"season_{season}={err}")

    if all_upcoming:
        # sort by kickoff time ascending
        all_upcoming.sort(key=lambda fx: parse_utc_datetime(fx["fixture"]["date"]))
        return all_upcoming[:limit], ""

    return [], " | ".join(diagnostics[:4])


async def get_api_status() -> dict:
    """
    Lightweight API-Football status probe.
    Returns:
      {
        "ok": bool,
        "errors": str,
        "results": int,
        "requests_remaining": str,
      }
    """
    url = f"{API_BASE_URL}/status"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=20) as resp:
                payload = await resp.json()
                remaining = (
                    resp.headers.get("X-RateLimit-Requests-Remaining")
                    or resp.headers.get("x-ratelimit-requests-remaining")
                    or resp.headers.get("X-RateLimit-Remaining")
                    or "unknown"
                )
                errors = _extract_api_errors(payload)
                return {
                    "ok": resp.status == 200 and not errors,
                    "errors": errors,
                    "results": len(payload.get("response", [])),
                    "requests_remaining": str(remaining),
                }
    except Exception as exc:
        return {
            "ok": False,
            "errors": str(exc),
            "results": 0,
            "requests_remaining": "unknown",
        }


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


async def get_fixture_by_id(fixture_id: int) -> dict:
    payload = await _api_get(f"{API_BASE_URL}/fixtures?id={fixture_id}", ttl_seconds=30)
    response = payload.get("response", [])
    return response[0] if response else {}


async def get_h2h(home_id: int, away_id: int, last: int = 5) -> str:
    payload = await _api_get(f"{API_BASE_URL}/fixtures/headtohead?h2h={home_id}-{away_id}&last={last}", ttl_seconds=1800)
    matches = payload.get("response", [])
    home_wins = 0
    away_wins = 0
    draws = 0
    for fixture in matches:
        hg = fixture.get("goals", {}).get("home")
        ag = fixture.get("goals", {}).get("away")
        if hg is None or ag is None:
            continue
        if hg > ag:
            home_wins += 1
        elif ag > hg:
            away_wins += 1
        else:
            draws += 1
    return f"{home_wins}-{draws}-{away_wins}"


def is_top_match(fixture: dict) -> bool:
    league_round = str(fixture.get("league", {}).get("round", "")).lower()
    league_name = str(fixture.get("league", {}).get("name", "")).lower()
    home = str(fixture.get("teams", {}).get("home", {}).get("name", "")).lower()
    away = str(fixture.get("teams", {}).get("away", {}).get("name", "")).lower()
    if any(tag in league_round for tag in ["final", "semi", "quarter", "playoff", "play-off"]):
        return True
    if any(tag in league_name for tag in ["champions league", "europa league"]):
        return True
    derby_keywords = ["derby", "clasico", "classique"]
    if any(tag in league_round for tag in derby_keywords):
        return True
    top_teams = ["real madrid", "barcelona", "manchester city", "arsenal", "liverpool", "bayern", "psg", "inter", "milan", "juventus"]
    if any(team in home for team in top_teams) and any(team in away for team in top_teams):
        return True
    return False


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
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=20) as resp:
                    payload = await resp.json()
                    if payload.get("errors"):
                        print(f"API-Football warning for {url}: {payload.get('errors')}")
                    _api_cache[url] = {
                        "expires_at": now + timedelta(seconds=ttl_seconds),
                        "payload": payload,
                    }
                    return payload
        except Exception as e:
            print(f"API request failed: {url}, error: {e}")
            return {}


async def _search_teams_raw(query: str):
    payload = await _api_get(f"{API_BASE_URL}/teams?search={query}", ttl_seconds=600)
    return payload.get("response", [])


def _looks_cyrillic(value: str) -> bool:
    return any("а" <= ch.lower() <= "я" or ch.lower() in {"і", "ң", "ғ", "ү", "ұ", "қ", "ө", "һ"} for ch in value)


def translit_cyrillic_to_latin(value: str) -> str:
    out = []
    for ch in value:
        lower = ch.lower()
        mapped = CYRILLIC_TO_LATIN.get(lower, ch)
        if ch.isupper() and mapped:
            out.append(mapped[:1].upper() + mapped[1:])
        else:
            out.append(mapped)
    return "".join(out)


def _merge_team_results(primary: list, secondary: list) -> list:
    merged = []
    seen_ids = set()
    for item in primary + secondary:
        team_id = item.get("team", {}).get("id")
        if team_id in seen_ids:
            continue
        seen_ids.add(team_id)
        merged.append(item)
    return merged


def _extract_api_errors(payload: dict) -> str:
    errors = payload.get("errors")
    if not errors:
        return ""
    if isinstance(errors, dict):
        parts = []
        for key, value in errors.items():
            if value:
                parts.append(f"{key}:{value}")
        return ", ".join(parts)
    return str(errors)