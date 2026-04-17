from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import LANGUAGES

MENU_TEXTS = {
    "ru": {
        "teams": "Мои команды ⚽",
        "add": "Добавить команду ➕",
        "today": "Сегодня 📅",
        "settings": "Настройки ⚙️",
    },
    "kk": {
        "teams": "Менің командаларым ⚽",
        "add": "Команда қосу ➕",
        "today": "Бүгін 📅",
        "settings": "Баптаулар ⚙️",
    },
    "en": {
        "teams": "My Teams ⚽",
        "add": "Add Team ➕",
        "today": "Today 📅",
        "settings": "Settings ⚙️",
    },
}


def main_menu(lang: str = "ru"):
    text_map = MENU_TEXTS.get(lang, MENU_TEXTS["en"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text_map["teams"]), KeyboardButton(text=text_map["add"])],
            [KeyboardButton(text=text_map["today"]), KeyboardButton(text=text_map["settings"])],
        ],
        resize_keyboard=True,
    )

def language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=f"lang_{k}") for k,v in LANGUAGES.items()]
    ])


def settings_kb(user):
    day_status = "ON" if user["notify_day_enabled"] else "OFF"
    before_status = "ON" if user["notify_before_enabled"] else "OFF"
    lineup_status = "ON" if user["notify_lineup_enabled"] else "OFF"
    quiet_status = "ON" if user["quiet_hours_enabled"] else "OFF"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Day notify: {day_status}",
                    callback_data="set_toggle_day",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Before match: {before_status}",
                    callback_data="set_toggle_before",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Lineups (1h): {lineup_status}",
                    callback_data="set_toggle_lineup",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Quiet hours: {quiet_status}",
                    callback_data="set_toggle_quiet",
                )
            ],
            [InlineKeyboardButton(text="Change day hour", callback_data="set_day_hour")],
            [InlineKeyboardButton(text="Change before minutes", callback_data="set_before_minutes")],
            [InlineKeyboardButton(text="Change quiet range", callback_data="set_quiet_range")],
            [InlineKeyboardButton(text="Change timezone", callback_data="set_timezone")],
        ]
    )