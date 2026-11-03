"""Small SQLite/PostgreSQL compatibility layer for the Flask application."""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = ROOT / DATA_DIR
DB_PATH = DATA_DIR / "data.sqlite"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = DATABASE_URL.startswith(("postgres://", "postgresql://"))
if DATABASE_URL and not USE_POSTGRES:
    raise RuntimeError("DATABASE_URL must be a PostgreSQL connection URL.")
if os.environ.get("REQUIRE_DATABASE_URL", "").lower() == "true" and not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL to the PostgreSQL database before starting this deployment.")


class HybridRow(dict):
    """A mapping row that also supports SQLite-style numeric indexing."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


class PgCursor:
    def __init__(self, cursor, lastrowid=None):
        self._cursor = cursor
        self.lastrowid = lastrowid
        self.rowcount = cursor.rowcount

    @staticmethod
    def _row(value):
        return HybridRow(value) if value is not None else None

    def fetchone(self):
        return self._row(self._cursor.fetchone())

    def fetchall(self):
        return [self._row(value) for value in self._cursor.fetchall()]


class PgConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql, params=()):
        sql = sql.replace("MAX(reported,", "GREATEST(reported,")
        sql = sql.replace(
            "CAST(strftime('%H',date_attempted) AS INTEGER)",
            "CAST(EXTRACT(HOUR FROM date_attempted::timestamp) AS INTEGER)",
        )
        sql = sql.replace("?", "%s")
        wants_id = bool(re.match(
            r"\s*INSERT\s+INTO\s+(users|attempts|user_achievements|chatbot_messages)\b",
            sql, re.IGNORECASE,
        )) and " RETURNING " not in sql.upper()
        if wants_id:
            sql = sql.rstrip().rstrip(";") + " RETURNING id"
        cursor = self._connection.execute(sql, params)
        lastrowid = cursor.fetchone()["id"] if wants_id else None
        return PgCursor(cursor, lastrowid)

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()


def connect(path=None):
    if not USE_POSTGRES:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(path or DB_PATH)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    import psycopg
    from psycopg.rows import dict_row

    con = psycopg.connect(
        DATABASE_URL,
        sslmode=os.environ.get("DB_SSLMODE", "require"),
        row_factory=dict_row,
        prepare_threshold=None,
    )
    return PgConnection(con)


def initialize_postgres():
    con = connect()
    statements = [
        """CREATE TABLE IF NOT EXISTS users (
          id BIGSERIAL PRIMARY KEY, username TEXT UNIQUE NOT NULL,
          password_hash TEXT NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text))""",
        """CREATE TABLE IF NOT EXISTS attempts (
          id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          square_order INTEGER NOT NULL, moves_made INTEGER NOT NULL, time_taken INTEGER NOT NULL,
          hints_used INTEGER NOT NULL DEFAULT 0, is_daily INTEGER NOT NULL DEFAULT 0,
          challenge_date TEXT, date_attempted TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
          mode TEXT NOT NULL DEFAULT 'scramble')""",
        """CREATE TABLE IF NOT EXISTS user_achievements (
          id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          achievement_key TEXT NOT NULL, earned_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text),
          UNIQUE(user_id, achievement_key))""",
        """CREATE TABLE IF NOT EXISTS game_sessions (
          id TEXT PRIMARY KEY, user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          square_order INTEGER NOT NULL, solved_grid TEXT NOT NULL, is_daily INTEGER NOT NULL DEFAULT 0,
          challenge_date TEXT, started_at BIGINT NOT NULL, moves_made INTEGER NOT NULL DEFAULT 0,
          hints_used INTEGER NOT NULL DEFAULT 0, completed_at BIGINT,
          mode TEXT NOT NULL DEFAULT 'scramble', attempts_used INTEGER NOT NULL DEFAULT 0)""",
        """CREATE TABLE IF NOT EXISTS chatbot_messages (
          id BIGSERIAL PRIMARY KEY, user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
          request_id TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('user','assistant')),
          game_title TEXT NOT NULL DEFAULT 'Ramanujan Magic Square', content TEXT NOT NULL,
          context_json TEXT, feedback TEXT, feedback_note TEXT, reported INTEGER NOT NULL DEFAULT 0,
          moderation_reason TEXT, created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP::text))""",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_streak INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS last_daily_date TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verify_token TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verify_token_expires BIGINT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires BIGINT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS chatbot_language TEXT NOT NULL DEFAULT 'en'",
        "ALTER TABLE game_sessions ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'scramble'",
        "ALTER TABLE game_sessions ADD COLUMN IF NOT EXISTS attempts_used INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS hints_used INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS is_daily INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS challenge_date TEXT",
        "ALTER TABLE attempts ADD COLUMN IF NOT EXISTS mode TEXT NOT NULL DEFAULT 'scramble'",
        "ALTER TABLE chatbot_messages ADD COLUMN IF NOT EXISTS feedback_note TEXT",
        "CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_attempts_square_order ON attempts(square_order)",
        "CREATE INDEX IF NOT EXISTS idx_attempts_daily ON attempts(is_daily, challenge_date, square_order)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_chatbot_user_created ON chatbot_messages(user_id,created_at)",
        "CREATE INDEX IF NOT EXISTS idx_chatbot_request ON chatbot_messages(request_id)",
        "CREATE INDEX IF NOT EXISTS idx_chatbot_flagged ON chatbot_messages(reported,moderation_reason)",
    ]
    try:
        for statement in statements:
            con.execute(statement)
        con.commit()
    except Exception:
        con._connection.rollback()
        raise
    finally:
        con.close()
