import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 8618587406))

LANGUAGES = {
    'ru': '🇷🇺 Русский',
    'kk': '🇰🇿 Қазақша',
    'en': '🇬🇧 English'
}

DEFAULT_TIMEZONE = "Asia/Almaty"
API_BASE_URL = "https://v3.football.api-sports.io"

I18N = {
    "ru": {
        "welcome": "Привет! Я помогу следить за футбольными матчами без спойлеров.\n\nВыбери язык:",
        "ask_city": "Напиши свой город (например: Almaty, Moscow, Astana).",
        "city_saved": "Город сохранен: <b>{city}</b>\nТвой часовой пояс: <b>{timezone}</b>",
        "main_hint": "Выбери действие в меню ниже.",
        "teams_empty": "У тебя пока нет избранных команд.",
        "team_added": "Команда <b>{team}</b> добавлена в избранное.",
        "team_removed": "Команда удалена из избранного.",
        "ask_team_query": "Напиши название команды для поиска.",
        "search_empty": "Команда не найдена. Попробуй другое название.",
        "select_team": "Выбери команду:",
        "today_empty": "Сегодня у твоих команд матчей не найдено.",
        "today_title": "Матчи сегодня:",
        "settings_title": "Настройки уведомлений:",
        "settings_saved": "Настройка обновлена.",
        "quiet_saved": "Тихие часы обновлены: {start}:00 - {end}:00",
        "ask_timezone": "Отправь таймзону в формате Region/City (например Europe/Moscow).",
        "timezone_saved": "Таймзона обновлена: <b>{timezone}</b>",
        "invalid_timezone": "Не удалось распознать таймзону. Пример: Europe/Moscow",
        "admin_denied": "Эта команда только для администратора.",
        "admin_stats": "Пользователей: <b>{users}</b>\nИзбранных команд: <b>{favorites}</b>",
        "broadcast_done": "Рассылка отправлена {sent}/{total} пользователям.",
        "broadcast_hint": "Отправь текст рассылки следующим сообщением.",
        "match_day": "Сегодня матч: <b>{home} - {away}</b>\nНачало в <b>{time}</b> ({tz})\nТурнир: {league}",
        "match_before": "Скоро матч: <b>{home} - {away}</b>\nДо начала: <b>{minutes} мин</b>\nСтарт в <b>{time}</b> ({tz})",
        "lineup_soon": "Через час матч <b>{home} - {away}</b>. Скоро ожидаются составы.",
        "time_changed": "Изменилось время матча <b>{home} - {away}</b>.\nНовое время: <b>{time}</b> ({tz})",
    },
    "kk": {
        "welcome": "Сәлем! Мен футбол матчтарын спойлерсіз бақылауға көмектесемін.\n\nТілді таңда:",
        "ask_city": "Қалаңды жаз (мысалы: Almaty, Moscow, Astana).",
        "city_saved": "Қала сақталды: <b>{city}</b>\nСенің уақыт белдеуің: <b>{timezone}</b>",
        "main_hint": "Төменгі мәзірден әрекетті таңда.",
        "teams_empty": "Таңдаулы командалар әлі жоқ.",
        "team_added": "<b>{team}</b> командасы таңдаулыға қосылды.",
        "team_removed": "Команда таңдаулыдан өшірілді.",
        "ask_team_query": "Іздеу үшін команда атауын жаз.",
        "search_empty": "Команда табылмады. Басқа атауды байқап көр.",
        "select_team": "Команданы таңда:",
        "today_empty": "Бүгін сенің командаларыңда матч жоқ.",
        "today_title": "Бүгінгі матчтар:",
        "settings_title": "Хабарлама баптаулары:",
        "settings_saved": "Баптау жаңартылды.",
        "quiet_saved": "Тыныш сағаттар жаңартылды: {start}:00 - {end}:00",
        "ask_timezone": "Уақыт белдеуін Region/City форматында жібер (мысалы Europe/Moscow).",
        "timezone_saved": "Уақыт белдеуі жаңартылды: <b>{timezone}</b>",
        "invalid_timezone": "Уақыт белдеуі танылмады. Мысал: Europe/Moscow",
        "admin_denied": "Бұл команда тек админге қолжетімді.",
        "admin_stats": "Пайдаланушылар: <b>{users}</b>\nТаңдаулы командалар: <b>{favorites}</b>",
        "broadcast_done": "Таратылым {sent}/{total} пайдаланушыға жіберілді.",
        "broadcast_hint": "Келесі хабарламада тарату мәтінін жібер.",
        "match_day": "Бүгін матч: <b>{home} - {away}</b>\nБасталуы: <b>{time}</b> ({tz})\nТурнир: {league}",
        "match_before": "Жақында матч: <b>{home} - {away}</b>\nБасталуына: <b>{minutes} мин</b>\nУақыты: <b>{time}</b> ({tz})",
        "lineup_soon": "<b>{home} - {away}</b> матчы 1 сағаттан кейін басталады. Құрамдар жақында шығады.",
        "time_changed": "<b>{home} - {away}</b> матчының уақыты өзгерді.\nЖаңа уақыт: <b>{time}</b> ({tz})",
    },
    "en": {
        "welcome": "Hi! I help you follow football matches with no spoilers.\n\nChoose language:",
        "ask_city": "Send your city (example: Almaty, Moscow, Astana).",
        "city_saved": "City saved: <b>{city}</b>\nYour timezone: <b>{timezone}</b>",
        "main_hint": "Choose an action from the menu below.",
        "teams_empty": "You have no favorite teams yet.",
        "team_added": "Team <b>{team}</b> was added to favorites.",
        "team_removed": "Team removed from favorites.",
        "ask_team_query": "Send a team name to search.",
        "search_empty": "Team not found. Try another name.",
        "select_team": "Choose a team:",
        "today_empty": "No matches for your teams today.",
        "today_title": "Today's matches:",
        "settings_title": "Notification settings:",
        "settings_saved": "Setting updated.",
        "quiet_saved": "Quiet hours updated: {start}:00 - {end}:00",
        "ask_timezone": "Send timezone in Region/City format (example: Europe/Moscow).",
        "timezone_saved": "Timezone updated: <b>{timezone}</b>",
        "invalid_timezone": "Could not parse timezone. Example: Europe/Moscow",
        "admin_denied": "This command is admin-only.",
        "admin_stats": "Users: <b>{users}</b>\nFavorite teams: <b>{favorites}</b>",
        "broadcast_done": "Broadcast sent to {sent}/{total} users.",
        "broadcast_hint": "Send broadcast text in your next message.",
        "match_day": "Match day: <b>{home} - {away}</b>\nKickoff at <b>{time}</b> ({tz})\nLeague: {league}",
        "match_before": "Upcoming match: <b>{home} - {away}</b>\nStarts in <b>{minutes} min</b>\nKickoff at <b>{time}</b> ({tz})",
        "lineup_soon": "Match <b>{home} - {away}</b> starts in 1 hour. Lineups are expected soon.",
        "time_changed": "Kickoff time changed for <b>{home} - {away}</b>.\nNew time: <b>{time}</b> ({tz})",
    },
}