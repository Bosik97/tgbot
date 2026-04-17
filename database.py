import sqlite3
from typing import Optional

conn = sqlite3.connect("bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
c = conn.cursor()


def init_db() -> None:
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            language TEXT DEFAULT 'ru',
            city TEXT,
            timezone TEXT,
            notify_day_enabled INTEGER DEFAULT 1,
            notify_day_hour INTEGER DEFAULT 9,
            notify_before_enabled INTEGER DEFAULT 1,
            notify_before_minutes INTEGER DEFAULT 180,
            notify_lineup_enabled INTEGER DEFAULT 1,
            quiet_hours_enabled INTEGER DEFAULT 0,
            quiet_start_hour INTEGER DEFAULT 23,
            quiet_end_hour INTEGER DEFAULT 8
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            team_id INTEGER,
            team_name TEXT,
            PRIMARY KEY (user_id, team_id)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS sent_notifications (
            user_id INTEGER,
            fixture_id INTEGER,
            notif_type TEXT,
            sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, fixture_id, notif_type)
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS fixture_snapshot (
            user_id INTEGER,
            fixture_id INTEGER,
            starts_at_utc TEXT,
            PRIMARY KEY (user_id, fixture_id)
        )
        """
    )
    conn.commit()

    # Lightweight migration for older DB versions.
    c.execute("PRAGMA table_info(users)")
    existing_columns = {row["name"] for row in c.fetchall()}
    required = {
        "notify_day_enabled": "INTEGER DEFAULT 1",
        "notify_day_hour": "INTEGER DEFAULT 9",
        "notify_before_enabled": "INTEGER DEFAULT 1",
        "notify_before_minutes": "INTEGER DEFAULT 180",
        "notify_lineup_enabled": "INTEGER DEFAULT 1",
        "quiet_hours_enabled": "INTEGER DEFAULT 0",
        "quiet_start_hour": "INTEGER DEFAULT 23",
        "quiet_end_hour": "INTEGER DEFAULT 8",
    }
    for column, ddl in required.items():
        if column not in existing_columns:
            c.execute(f"ALTER TABLE users ADD COLUMN {column} {ddl}")
    conn.commit()


def get_user(user_id: int) -> Optional[sqlite3.Row]:
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    return c.fetchone()


def ensure_user(user_id: int, username: Optional[str] = None) -> sqlite3.Row:
    user = get_user(user_id)
    if user is None:
        c.execute(
            "INSERT INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        conn.commit()
        return get_user(user_id)
    if username and username != user["username"]:
        c.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
        conn.commit()
        return get_user(user_id)
    return user


def update_user(
    user_id: int,
    language: Optional[str] = None,
    city: Optional[str] = None,
    timezone: Optional[str] = None,
    notify_day_enabled: Optional[int] = None,
    notify_day_hour: Optional[int] = None,
    notify_before_enabled: Optional[int] = None,
    notify_before_minutes: Optional[int] = None,
    notify_lineup_enabled: Optional[int] = None,
    quiet_hours_enabled: Optional[int] = None,
    quiet_start_hour: Optional[int] = None,
    quiet_end_hour: Optional[int] = None,
) -> None:
    updates = []
    values = []
    payload = {
        "language": language,
        "city": city,
        "timezone": timezone,
        "notify_day_enabled": notify_day_enabled,
        "notify_day_hour": notify_day_hour,
        "notify_before_enabled": notify_before_enabled,
        "notify_before_minutes": notify_before_minutes,
        "notify_lineup_enabled": notify_lineup_enabled,
        "quiet_hours_enabled": quiet_hours_enabled,
        "quiet_start_hour": quiet_start_hour,
        "quiet_end_hour": quiet_end_hour,
    }
    for field, value in payload.items():
        if value is not None:
            updates.append(f"{field}=?")
            values.append(value)

    if not updates:
        return
    values.append(user_id)
    c.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id=?", values)
    conn.commit()


def add_favorite(user_id: int, team_id: int, team_name: str) -> None:
    c.execute(
        "INSERT OR IGNORE INTO favorites VALUES (?,?,?)",
        (user_id, team_id, team_name),
    )
    conn.commit()


def remove_favorite(user_id: int, team_id: int) -> None:
    c.execute("DELETE FROM favorites WHERE user_id=? AND team_id=?", (user_id, team_id))
    conn.commit()


def get_favorites(user_id: int):
    c.execute("SELECT team_id, team_name FROM favorites WHERE user_id=?", (user_id,))
    return c.fetchall()


def get_all_users():
    c.execute("SELECT * FROM users")
    return c.fetchall()


def get_users_count() -> int:
    c.execute("SELECT COUNT(*) AS total FROM users")
    return int(c.fetchone()["total"])


def get_favorites_count() -> int:
    c.execute("SELECT COUNT(*) AS total FROM favorites")
    return int(c.fetchone()["total"])


def was_notification_sent(user_id: int, fixture_id: int, notif_type: str) -> bool:
    c.execute(
        "SELECT 1 FROM sent_notifications WHERE user_id=? AND fixture_id=? AND notif_type=?",
        (user_id, fixture_id, notif_type),
    )
    return c.fetchone() is not None


def mark_notification_sent(user_id: int, fixture_id: int, notif_type: str) -> None:
    c.execute(
        """
        INSERT OR IGNORE INTO sent_notifications (user_id, fixture_id, notif_type)
        VALUES (?, ?, ?)
        """,
        (user_id, fixture_id, notif_type),
    )
    conn.commit()


def get_fixture_snapshot(user_id: int, fixture_id: int) -> Optional[str]:
    c.execute(
        "SELECT starts_at_utc FROM fixture_snapshot WHERE user_id=? AND fixture_id=?",
        (user_id, fixture_id),
    )
    row = c.fetchone()
    return row["starts_at_utc"] if row else None


def set_fixture_snapshot(user_id: int, fixture_id: int, starts_at_utc: str) -> None:
    c.execute(
        """
        INSERT INTO fixture_snapshot (user_id, fixture_id, starts_at_utc)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, fixture_id) DO UPDATE SET starts_at_utc=excluded.starts_at_utc
        """,
        (user_id, fixture_id, starts_at_utc),
    )
    conn.commit()