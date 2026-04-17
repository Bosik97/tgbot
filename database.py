import sqlite3
from datetime import datetime

conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    language TEXT DEFAULT 'ru',
    city TEXT,
    timezone TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER,
    team_id INTEGER,
    team_name TEXT,
    league_id INTEGER,
    PRIMARY KEY (user_id, team_id)
)''')

conn.commit()

def get_user(user_id):
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()

def save_user(user_id, username, city=None, timezone=None, language='ru'):
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?)", 
              (user_id, username, language, city, timezone))
    conn.commit()
