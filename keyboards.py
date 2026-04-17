from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu(lang='ru'):
    texts = {
        'ru': ["Мои команды ⚽", "Добавить команду ➕", "Сегодняшние матчи 📅", "Настройки ⚙️"],
        'kk': ["Менің командаларым ⚽", "Команда қосу ➕", "Бүгінгі матчтар 📅", "Параметрлер ⚙️"],
        'en': ["My Teams ⚽", "Add Team ➕", "Today's Matches 📅", "Settings ⚙️"]
    }
    t = texts.get(lang, texts['ru'])
    kb = [[KeyboardButton(text)] for text in t]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def language_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=f"lang_{k}") for k, v in LANGUAGES.items()]
    ])
    return kb
