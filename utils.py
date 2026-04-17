import aiohttp
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import pytz
from config import API_FOOTBALL_KEY

headers = {"x-apisports-key": API_FOOTBALL_KEY}

async def search_teams(query):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://v3.football.api-sports.io/teams?search={query}", headers=headers) as resp:
            return (await resp.json()).get("response", [])[:8]

async def get_fixtures(team_id):
    today = datetime.now().strftime("%Y-%m-%d")
    async with aiohttp.ClientSession() as session:
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&from={today}&to={(datetime.now()+timedelta(days=30)).strftime('%Y-%m-%d')}"
        async with session.get(url, headers=headers) as resp:
            return (await resp.json()).get("response", [])

async def get_city_timezone(city):
    try:
        geo = Nominatim(user_agent="football_bot")
        loc = geo.geocode(city)
        if loc:
            return pytz.country_timezones.get(loc.raw.get("country_code", "KZ").upper(), ["Asia/Almaty"])[0]
    except:
        pass
    return "Asia/Almaty"