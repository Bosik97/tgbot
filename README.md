# Football Match Reminder Bot

Telegram bot on `aiogram` with local-time match notifications via API-Football.

## Features

- Multi-language UI: Russian, Kazakh, English.
- Team search and favorites list.
- Match reminders in the user's local timezone.
- Two reminder modes:
  - match day reminder at configurable hour,
  - before-match reminder (configurable minutes).
- Lineup reminder 1 hour before kickoff.
- Match kickoff-time change notification.
- Quiet hours mode (no notifications in selected hour range).
- Admin commands: stats and broadcast.

## Stack

- Python + aiogram
- API-Football
- SQLite
- APScheduler
- Railway deployment ready

## Environment Variables

Create `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
API_FOOTBALL_KEY=your_api_football_key
ADMIN_ID=123456789
```

## Local Run

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start bot:

```bash
python main.py
```

## Railway Deploy

1. Push project to GitHub.
2. Create a new Railway project from that repository.
3. Set environment variables in Railway service settings:
   - `BOT_TOKEN`
   - `API_FOOTBALL_KEY`
   - `ADMIN_ID`
4. Start command:

```bash
python main.py
```

## User Flow

- `/start`
- Choose language
- Send city
- Add favorite teams
- Open settings and configure reminders/timezone/quiet hours

## Admin Commands

- `/admin` - users and favorites stats
- `/broadcast` - send message to all users
