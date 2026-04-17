import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ADMIN_ID = 8618587406  # твой ID (можно изменить)

LANGUAGES = {
    'ru': '🇷🇺 Русский',
    'kk': '🇰🇿 Қазақша',
    'en': '🇬🇧 English'
}

DEFAULT_LANGUAGE = 'ru'
