from datetime import datetime, timedelta, timezone
import pytz
from config import DEFAULT_TIMEZONE, I18N, LANGUAGES

# Translation helper
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

# Top match detection (works with both API and local fixture formats)
def is_top_match(fixture: dict) -> bool:
    league_round = ""
    league_name = ""
    home = ""
    away = ""

    if "league" in fixture:
        if isinstance(fixture["league"], dict):
            league_round = str(fixture["league"].get("round", "")).lower()
            league_name = str(fixture["league"].get("name", "")).lower()
        else:
            league_name = str(fixture["league"]).lower()
    if "round" in fixture:
        league_round = str(fixture.get("round", "")).lower()

    if "teams" in fixture and isinstance(fixture["teams"], dict):
        home = str(fixture["teams"].get("home", {}).get("name", "")).lower()
        away = str(fixture["teams"].get("away", {}).get("name", "")).lower()
    else:
        home = str(fixture.get("home_team_name", "")).lower()
        away = str(fixture.get("away_team_name", "")).lower()

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

# Cyrillic transliteration helpers (kept for potential future use)
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

# City to timezone mapping (local, no external API)
CITY_TZ_OVERRIDES_LOCAL = {
    "almaty": "Asia/Almaty",
    "astana": "Asia/Almaty",
    "moscow": "Europe/Moscow",
    "saint petersburg": "Europe/Moscow",
    "spb": "Europe/Moscow",
    "shymkent": "Asia/Almaty",
    "aktobe": "Asia/Aqtobe",
    "atyrau": "Asia/Atyrau",
    "karaganda": "Asia/Almaty",
    "nur-sultan": "Asia/Almaty",
    "astana": "Asia/Almaty",
}

def get_city_timezone(city: str):
    key = city.strip().lower()
    return CITY_TZ_OVERRIDES_LOCAL.get(key, DEFAULT_TIMEZONE)
