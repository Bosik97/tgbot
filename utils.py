from datetime import datetime, timedelta, timezone
import pytz
import aiohttp
from config import DEFAULT_TIMEZONE, I18N, LANGUAGES, FOOTBALL_DATA_BASE_URL, API_FOOTBALL_KEY, API_BASE_URL

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
}

def get_city_timezone(city: str):
    key = city.strip().lower()
    return CITY_TZ_OVERRIDES_LOCAL.get(key, DEFAULT_TIMEZONE)

# Top match detection
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

# ========== API FOOTBALL ==========
async def fetch_fixtures_from_api(date_str: str) -> list:
    """Fetch fixtures from API Football for a given date (YYYY-MM-DD)"""
    if not API_FOOTBALL_KEY:
        print("[API] No API key provided")
        return []

    url = f"{API_BASE_URL}/fixtures"
    headers = {
        'x-rapidapi-key': API_FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    params = {'date': date_str}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                if resp.status != 200:
                    print(f"[API] HTTP {resp.status}")
                    return []
                data = await resp.json()
                fixtures = []
                for fixture in data.get('response', []):
                    fixture_data = fixture.get('fixture', {})
                    teams = fixture.get('teams', {})
                    league = fixture.get('league', {})
                    goals = fixture.get('goals', {})

                    fixtures.append({
                        "home_team_name": teams.get('home', {}).get('name', ''),
                        "away_team_name": teams.get('away', {}).get('name', ''),
                        "league": league.get('name', ''),
                        "match_date_utc": fixture_data.get('date', ''),
                        "status": fixture_data.get('status', {}).get('short', ''),
                        "score_home": goals.get('home'),
                        "score_away": goals.get('away'),
                    })
                return fixtures
    except Exception as e:
        print(f"[API] Error: {e}")
        return []


# ========== SCRAPING: ESPN ==========
async def _scrape_espn_matches(date_str: str) -> list:
    """Scrape matches from ESPN public API (no key required)"""
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard?dates={date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                events = data.get("events", [])
                fixtures = []
                for ev in events:
                    comp = ev.get("competitions", [{}])[0]
                    teams = comp.get("competitors", [])
                    if len(teams) < 2:
                        continue
                    home = next((t for t in teams if t.get("homeAway") == "home"), teams[0])
                    away = next((t for t in teams if t.get("homeAway") == "away"), teams[1])
                    fixtures.append({
                        "home_team_name": home.get("team", {}).get("displayName", ""),
                        "away_team_name": away.get("team", {}).get("displayName", ""),
                        "league": comp.get("competition", {}).get("name", ""),
                        "match_date_utc": ev.get("date", ""),
                        "status": ev.get("status", {}).get("type", ""),
                        "score_home": home.get("score"),
                        "score_away": away.get("score"),
                    })
                return fixtures
    except Exception as e:
        print(f"[SCRAPER ESPN] Error: {e}")
        return []

# ========== SCRAPING: football-data.org (public HTML) ==========
async def _scrape_football_data_matches(date_str: str) -> list:
    """Scrape matches from football-data.org (public JSON without key, heavily rate-limited)"""
    # Football-data.org requires API key even for public endpoints now
    return []

# ========== SCRAPING: SofaScore (public) ==========
async def _scrape_sofascore_matches(date_str: str) -> list:
    """Scrape from SofaScore public API (may work without key)"""
    url = f"https://api.sofascore.com/api/v1/match-date/{date_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                events = data.get("events", [])
                fixtures = []
                for ev in events:
                    home = ev.get("homeTeam", {})
                    away = ev.get("awayTeam", {})
                    fixtures.append({
                        "home_team_name": home.get("name", ""),
                        "away_team_name": away.get("name", ""),
                        "league": ev.get("tournament", {}).get("name", ""),
                        "match_date_utc": ev.get("startTime", ""),
                        "status": ev.get("status", {}).get("type", ""),
                        "score_home": ev.get("homeScore", {}).get("current"),
                        "score_away": ev.get("awayScore", {}).get("current"),
                    })
                return fixtures
    except Exception as e:
        print(f"[SCRAPER SofaScore] Error: {e}")
        return []

# ========== MAIN FETCHER ==========
async def fetch_fixtures_from_web(date_str: str) -> list:
    """
    Try multiple sources to get fixtures for a given date (YYYY-MM-DD).
    Returns list of fixture dicts compatible with local DB schema.
    Order: API Football -> ESPN -> SofaScore -> empty
    """
    fixtures = await fetch_fixtures_from_api(date_str)
    if fixtures:
        print(f"[API] Fixtures: {len(fixtures)}")
        return fixtures

    fixtures = await _scrape_espn_matches(date_str)
    if fixtures:
        print(f"[SCRAPER] ESPN: {len(fixtures)} fixtures")
        return fixtures

    fixtures = await _scrape_sofascore_matches(date_str)
    if fixtures:
        print(f"[SCRAPER] SofaScore: {len(fixtures)} fixtures")
        return fixtures

    print(f"[FETCHER] All sources failed for {date_str}")
    return []

# ========== TEAM SEARCH VIA API ==========
async def search_teams_api(query: str) -> list:
    """Search teams via API Football"""
    if not API_FOOTBALL_KEY:
        return []

    url = f"{API_BASE_URL}/teams"
    headers = {
        'x-rapidapi-key': API_FOOTBALL_KEY,
        'x-rapidapi-host': 'v3.football.api-sports.io'
    }
    params = {'search': query}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                results = []
                seen_ids = set()
                for team_data in data.get('response', []):
                    team = team_data.get('team', {})
                    tid = team.get('id')
                    name = team.get('name', '')
                    if tid and name and tid not in seen_ids:
                        results.append({"team": {"id": tid, "name": name}})
                        seen_ids.add(tid)
                return results[:8]
    except Exception as e:
        print(f"[API TEAM] Error: {e}")
        return []


# ========== TEAM SEARCH VIA WEB ==========
async def search_teams_web(query: str) -> list:
    """
    Search teams via web scrapers (no API key).
    Returns list of {'team': {'id': ..., 'name': ...}}
    """
    # Try ESPN team search
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/teams?search={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    teams_container = data.get("sports", [{}])[0].get("leagues", [{}])[0].get("teams", [])
                    results = []
                    seen_ids = set()
                    for t in teams_container:
                        team = t.get("team", {})
                        tid = team.get("id")
                        name = team.get("displayName", "")
                        if tid and name and tid not in seen_ids:
                            results.append({"team": {"id": tid, "name": name}})
                            seen_ids.add(tid)
                    return results[:8]
    except Exception as e:
        print(f"[SCRAPER TEAM] ESPN error: {e}")

    # Try football-data teams endpoint (requires key, skip)
    return []

# ========== TEAM SEARCH ==========
async def search_teams(query: str) -> list:
    """Search teams: try API first, then web scrapers, then fallback to alias mapping."""
    results = await search_teams_api(query)
    if results:
        return results

    results = await search_teams_web(query)
    if results:
        return results

    # Fallback: local alias mapping
    alias_map = {
        "челси": "chelsea", "ман сити": "manchester city", "манчестер сити": "manchester city",
        "ман юнайтед": "manchester united", "манчестер юнайтед": "manchester united",
        "ливерпуль": "liverpool", "арсенал": "arsenal", "тоттенхэм": "tottenham",
        "барселона": "barcelona", "реал": "real madrid", "реал мадрид": "real madrid",
        "атлетико": "atletico madrid", "бавария": "bayern munich", "псж": "paris saint germain",
        "интер": "inter", "милан": "milan", "ювентус": "juventus",
    }
    mapped_name = alias_map.get(query.lower())
    if mapped_name:
        return [{"team": {"id": 0, "name": mapped_name}}]
    return []
