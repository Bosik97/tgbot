from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import LANGUAGES

def main_menu(lang='ru'):
    texts = {
        'ru': ["Мои команды ⚽", "Добавить команду ➕", "Сегодня 📅", "Настройки ⚙️"],
        'kk': ["Менің командаларым ⚽", "Команда қосу ➕", "Бүгін 📅", "Параметрлер ⚙️"],
        'en': ["My Teams ⚽", "Add Team ➕", "Today 📅", "Settings ⚙️"]
    }
    t = texts.get(lang, texts['ru'])
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(i)] for i in t], resize_keyboard=True)

def language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=f"lang_{k}") for k,v in LANGUAGES.items()]
    ])