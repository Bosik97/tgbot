import aiohttp
import pytz
from datetime import datetime
from geopy.geocoders import Nominatim
from config import API_FOOTBALL_KEY

headers = {"x-apisports-key": API_FOOTBALL_KEY}

async def get_teams(search):
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://v3.football.api-sports.io/teams?search={search}", headers=headers) as resp:
            return (await resp.json()).get('response', [])

async def get_fixtures_by_team(team_id, date_from, date_to):
    async with aiohttp.ClientSession() as session:
        url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&from={date_from}&to={date_to}"
        async with session.get(url, headers=headers) as resp:
            return (await resp.json()).get('response', [])

async def get_timezone(city):
    geolocator = Nominatim(user_agent="football_bot")
    location = geolocator.geocode(city)
    if location:
        tz = pytz.timezone(pytz.country_timezones.get(location.raw.get('country_code'), ['UTC'])[0])
        return str(tz)
    return 'Asia/Almaty'  # default
