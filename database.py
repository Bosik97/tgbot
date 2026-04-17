import sqlite3
from typing import Optional

conn = sqlite3.connect("bot.db", check_same_thread=False)
conn.row_factory = sqlite3.Row
c = conn.cursor()


def init_db() -> None:
    # Users table
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
            quiet_end_hour INTEGER DEFAULT 8,
            notify_profile TEXT DEFAULT 'standard',
            live_events_enabled INTEGER DEFAULT 0,
            spoiler_mode INTEGER DEFAULT 0
        )
        """
    )

    # Favorites table (using team_name without team_id)
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER,
            team_name TEXT,
            PRIMARY KEY (user_id, team_name)
        )
        """
    )

    # Migration: if old favorites table with team_id exists, convert it
    c.execute("PRAGMA table_info(favorites)")
    columns = [row["name"] for row in c.fetchall()]
    if "team_id" in columns:
        # Copy data to new table
        c.execute("SELECT user_id, team_name FROM favorites")
        rows = c.fetchall()
        # Drop old table
        c.execute("DROP TABLE favorites")
        # Recreate new
        c.execute(
            """
            CREATE TABLE favorites (
                user_id INTEGER,
                team_name TEXT,
                PRIMARY KEY (user_id, team_name)
            )
            """
        )
        for row in rows:
            c.execute("INSERT INTO favorites (user_id, team_name) VALUES (?, ?)", (row["user_id"], row["team_name"]))
        conn.commit()

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
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS fixtures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team_name TEXT NOT NULL,
            away_team_name TEXT NOT NULL,
            league TEXT,
            match_date_utc TEXT NOT NULL,
            status TEXT DEFAULT 'scheduled',
            score_home INTEGER,
            score_away INTEGER,
            round TEXT,
            added_by INTEGER
        )
        """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_date ON fixtures(match_date_utc)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_fixtures_teams ON fixtures(home_team_name, away_team_name)")

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            user_id INTEGER,
            fixture_id INTEGER,
            prediction TEXT,
            points INTEGER DEFAULT 0,
            settled INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, fixture_id)
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS friends (
            user_id INTEGER,
            friend_id INTEGER,
            PRIMARY KEY (user_id, friend_id)
        )
        """
    )
    conn.commit()

    # Migrate user table columns
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
        "notify_profile": "TEXT DEFAULT 'standard'",
        "live_events_enabled": "INTEGER DEFAULT 0",
        "spoiler_mode": "INTEGER DEFAULT 0",
    }
    for column, ddl in required.items():
        if column not in existing_columns:
            c.execute(f"ALTER TABLE users ADD COLUMN {column} {ddl}")
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
        "notify_profile": "TEXT DEFAULT 'standard'",
        "live_events_enabled": "INTEGER DEFAULT 0",
        "spoiler_mode": "INTEGER DEFAULT 0",
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
    notify_profile: Optional[str] = None,
    live_events_enabled: Optional[int] = None,
    spoiler_mode: Optional[int] = None,
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
        "notify_profile": notify_profile,
        "live_events_enabled": live_events_enabled,
        "spoiler_mode": spoiler_mode,
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


def add_favorite(user_id: int, team_name: str) -> None:
    c.execute(
        "INSERT OR IGNORE INTO favorites (user_id, team_name) VALUES (?, ?)",
        (user_id, team_name),
    )
    conn.commit()


def remove_favorite(user_id: int, team_name: str) -> None:
    c.execute("DELETE FROM favorites WHERE user_id=? AND team_name=?", (user_id, team_name))
    conn.commit()


def get_favorites(user_id: int):
    c.execute("SELECT team_name FROM favorites WHERE user_id=?", (user_id,))
    rows = c.fetchall()
    return [row["team_name"] for row in rows]


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


def save_prediction(user_id: int, fixture_id: int, prediction: str) -> None:
    c.execute(
        """
        INSERT INTO predictions (user_id, fixture_id, prediction)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, fixture_id) DO UPDATE SET prediction=excluded.prediction
        """,
        (user_id, fixture_id, prediction),
    )
    conn.commit()


def get_unsettled_predictions():
    c.execute("SELECT * FROM predictions WHERE settled=0")
    return c.fetchall()


def settle_prediction(user_id: int, fixture_id: int, points: int) -> None:
    c.execute(
        "UPDATE predictions SET points=?, settled=1 WHERE user_id=? AND fixture_id=?",
        (points, user_id, fixture_id),
    )
    conn.commit()


def add_fixture(
    home_team_name: str,
    away_team_name: str,
    league: str,
    match_date_utc: str,
    status: str = "scheduled",
    score_home: int = None,
    score_away: int = None,
    round: str = None,
    added_by: int = None,
) -> int:
    c.execute(
        """
        INSERT INTO fixtures (home_team_name, away_team_name, league, match_date_utc, status, score_home, score_away, round, added_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (home_team_name, away_team_name, league, match_date_utc, status, score_home, score_away, round, added_by),
    )
    conn.commit()
    return c.lastrowid


def get_fixture_by_local_id(fixture_id: int):
    c.execute("SELECT * FROM fixtures WHERE id=?", (fixture_id,))
    return c.fetchone()


def update_fixture_score(fixture_id: int, score_home: int, score_away: int, status: str = None):
    if status:
        c.execute("UPDATE fixtures SET score_home=?, score_away=?, status=? WHERE id=?", (score_home, score_away, status, fixture_id))
    else:
        c.execute("UPDATE fixtures SET score_home=?, score_away=? WHERE id=?", (score_home, score_away, fixture_id))
    conn.commit()


def delete_fixture(fixture_id: int):
    c.execute("DELETE FROM fixtures WHERE id=?", (fixture_id,))
    conn.commit()


def get_fixtures_by_team(team_name: str, days: int = 30):
    from datetime import datetime, timedelta, timezone
    now_utc = datetime.now(timezone.utc)
    until_utc = now_utc + timedelta(days=days)
    c.execute(
        """
        SELECT * FROM fixtures
        WHERE (home_team_name LIKE ? OR away_team_name LIKE ?)
          AND match_date_utc >= ? AND match_date_utc <= ?
          AND status != 'finished'
        ORDER BY match_date_utc ASC
        """,
        (f"%{team_name}%", f"%{team_name}%", now_utc.isoformat(), until_utc.isoformat()),
    )
    return c.fetchall()


def get_all_upcoming_fixtures(limit: int = 50):
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    c.execute(
        """
        SELECT * FROM fixtures
        WHERE match_date_utc >= ? AND status != 'finished'
        ORDER BY match_date_utc ASC
        LIMIT ?
        """,
        (now_utc.isoformat(), limit),
    )
    return c.fetchall()


def get_fixtures_in_range(start_date_utc: str, end_date_utc: str):
    c.execute(
        """
        SELECT * FROM fixtures
        WHERE match_date_utc >= ? AND match_date_utc <= ?
        ORDER BY match_date_utc ASC
        """,
        (start_date_utc, end_date_utc),
    )
    return c.fetchall()


def get_last_fixtures_by_team(team_name: str, count: int = 5):
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc)
    c.execute(
        """
        SELECT * FROM fixtures
        WHERE (home_team_name LIKE ? OR away_team_name LIKE ?)
          AND match_date_utc <= ?
          AND status = 'finished'
        ORDER BY match_date_utc DESC
        LIMIT ?
        """,
        (f"%{team_name}%", f"%{team_name}%", now_utc.isoformat(), count),
    )
    return c.fetchall()


def get_all_fixtures_count() -> int:
    c.execute("SELECT COUNT(*) AS total FROM fixtures")
    return int(c.fetchone()["total"])


# Notification tracking functions
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


# Predictions functions
def save_prediction(user_id: int, fixture_id: int, prediction: str) -> None:
    c.execute(
        """
        INSERT INTO predictions (user_id, fixture_id, prediction)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, fixture_id) DO UPDATE SET prediction=excluded.prediction
        """,
        (user_id, fixture_id, prediction),
    )
    conn.commit()


def get_unsettled_predictions():
    c.execute("SELECT * FROM predictions WHERE settled=0")
    return c.fetchall()


def settle_prediction(user_id: int, fixture_id: int, points: int) -> None:
    c.execute(
        "UPDATE predictions SET points=?, settled=1 WHERE user_id=? AND fixture_id=?",
        (points, user_id, fixture_id),
    )
    conn.commit()


def get_total_points(user_id: int) -> int:
    c.execute("SELECT COALESCE(SUM(points), 0) AS total FROM predictions WHERE user_id=?", (user_id,))
    return int(c.fetchone()["total"])


# Friends functions
def add_friend(user_id: int, friend_id: int) -> None:
    c.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
    conn.commit()


def get_friends(user_id: int):
    c.execute("SELECT friend_id FROM friends WHERE user_id=?", (user_id,))
    return [row["friend_id"] for row in c.fetchall()]


def get_all_fixtures_count() -> int:
    c.execute("SELECT COUNT(*) AS total FROM fixtures")
    return int(c.fetchone()["total"])


def add_friend(user_id: int, friend_id: int) -> None:
    c.execute("INSERT OR IGNORE INTO friends (user_id, friend_id) VALUES (?, ?)", (user_id, friend_id))
    conn.commit()


def get_friends(user_id: int):
    c.execute("SELECT friend_id FROM friends WHERE user_id=?", (user_id,))
    return [row["friend_id"] for row in c.fetchall()]