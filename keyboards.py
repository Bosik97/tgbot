from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import I18N, LANGUAGES

MENU_TEXTS = {
    "ru": {
        "teams": "Мои команды ⚽",
        "add": "Добавить команду ➕",
        "today": "Сегодня 📅",
        "next5": I18N["ru"]["next5_button"],
        "center": "Матч-центр 🎯",
        "weekend": "Мой уикенд 🗓",
        "fantasy": "Фэнтези-помощник 🧠",
        "league": "Мини-лига 🏆",
        "settings": "Настройки ⚙️",
    },
    "kk": {
        "teams": "Менің командаларым ⚽",
        "add": "Команда қосу ➕",
        "today": "Бүгін 📅",
        "next5": I18N["kk"]["next5_button"],
        "center": "Матч-орталық 🎯",
        "weekend": "Менің уикендім 🗓",
        "fantasy": "Фэнтези көмекші 🧠",
        "league": "Мини-лига 🏆",
        "settings": "Баптаулар ⚙️",
    },
    "en": {
        "teams": "My Teams ⚽",
        "add": "Add Team ➕",
        "today": "Today 📅",
        "next5": I18N["en"]["next5_button"],
        "center": "Match Center 🎯",
        "weekend": "My Weekend 🗓",
        "fantasy": "Fantasy Helper 🧠",
        "league": "Mini League 🏆",
        "settings": "Settings ⚙️",
    },
}


def main_menu(lang: str = "ru"):
    text_map = MENU_TEXTS.get(lang, MENU_TEXTS["en"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text_map["teams"]), KeyboardButton(text=text_map["add"])],
            [KeyboardButton(text=text_map["today"]), KeyboardButton(text=text_map["next5"])],
            [KeyboardButton(text=text_map["center"]), KeyboardButton(text=text_map["weekend"])],
            [KeyboardButton(text=text_map["fantasy"]), KeyboardButton(text=text_map["league"])],
            [KeyboardButton(text=text_map["settings"])],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
        is_persistent=True,
        input_field_placeholder="Выбери действие",
    )

def language_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=v, callback_data=f"lang_{k}") for k,v in LANGUAGES.items()]
    ])


def settings_kb(user):
    return settings_kb_localized(user, "en")


def settings_kb_localized(user, lang: str):
    status_text = {
        "ru": ("ВКЛ", "ВЫКЛ"),
        "kk": ("ҚОС", "ӨШІК"),
        "en": ("ON", "OFF"),
    }
    labels = {
        "ru": {
            "day_notify": "Уведомление в день матча",
            "before_match": "Перед матчем",
            "lineups": "Составы (1ч)",
            "quiet": "Тихие часы",
            "change_day_hour": "Изменить час дневного уведомления",
            "change_before_minutes": "Изменить минуты до матча",
            "change_quiet_range": "Изменить тихие часы",
            "change_timezone": "Изменить таймзону",
            "profile_calm": "Профиль: Спокойный",
            "profile_standard": "Стандарт",
            "profile_hardcore": "Хардкор",
            "live_events": "Live-события ВКЛ/ВЫКЛ",
        },
        "kk": {
            "day_notify": "Матч күні хабарлама",
            "before_match": "Матчқа дейін",
            "lineups": "Құрамдар (1сағ)",
            "quiet": "Тыныш сағаттар",
            "change_day_hour": "Күндізгі хабарлама уақытын өзгерту",
            "change_before_minutes": "Матчқа дейінгі минуттарды өзгерту",
            "change_quiet_range": "Тыныш сағаттарды өзгерту",
            "change_timezone": "Уақыт белдеуін өзгерту",
            "profile_calm": "Профиль: Тыныш",
            "profile_standard": "Стандарт",
            "profile_hardcore": "Хардкор",
            "live_events": "Live-оқиғалар ҚОС/ӨШІК",
        },
        "en": {
            "day_notify": "Day notify",
            "before_match": "Before match",
            "lineups": "Lineups (1h)",
            "quiet": "Quiet hours",
            "change_day_hour": "Change day hour",
            "change_before_minutes": "Change before minutes",
            "change_quiet_range": "Change quiet range",
            "change_timezone": "Change timezone",
            "profile_calm": "Profile: Calm",
            "profile_standard": "Standard",
            "profile_hardcore": "Hardcore",
            "live_events": "Live events ON/OFF",
        },
    }
    lang_pack = labels.get(lang, labels["en"])
    on_text, off_text = status_text.get(lang, status_text["en"])
    day_status = on_text if user["notify_day_enabled"] else off_text
    before_status = on_text if user["notify_before_enabled"] else off_text
    lineup_status = on_text if user["notify_lineup_enabled"] else off_text
    quiet_status = on_text if user["quiet_hours_enabled"] else off_text
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{lang_pack['day_notify']}: {day_status}",
                    callback_data="set_toggle_day",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{lang_pack['before_match']}: {before_status}",
                    callback_data="set_toggle_before",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{lang_pack['lineups']}: {lineup_status}",
                    callback_data="set_toggle_lineup",
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{lang_pack['quiet']}: {quiet_status}",
                    callback_data="set_toggle_quiet",
                )
            ],
            [InlineKeyboardButton(text=lang_pack["change_day_hour"], callback_data="set_day_hour")],
            [InlineKeyboardButton(text=lang_pack["change_before_minutes"], callback_data="set_before_minutes")],
            [InlineKeyboardButton(text=lang_pack["change_quiet_range"], callback_data="set_quiet_range")],
            [InlineKeyboardButton(text=lang_pack["change_timezone"], callback_data="set_timezone")],
            [
                InlineKeyboardButton(text=lang_pack["profile_calm"], callback_data="set_profile_calm"),
                InlineKeyboardButton(text=lang_pack["profile_standard"], callback_data="set_profile_standard"),
                InlineKeyboardButton(text=lang_pack["profile_hardcore"], callback_data="set_profile_hardcore"),
            ],
            [InlineKeyboardButton(text=lang_pack["live_events"], callback_data="set_toggle_live_events")],
        ]
    )