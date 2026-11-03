"""SQLite and MySQL connections for the Flask application."""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
if not DATA_DIR.is_absolute():
    DATA_DIR = ROOT / DATA_DIR
DB_PATH = DATA_DIR / "data.sqlite"
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_MYSQL = DATABASE_URL.startswith(("mysql://", "mysql+pymysql://"))
if DATABASE_URL and not USE_MYSQL:
    raise RuntimeError("DATABASE_URL must be a MySQL connection URL.")
if os.environ.get("REQUIRE_DATABASE_URL", "").lower() == "true" and not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL to the production database before starting this deployment.")


class HybridRow(dict):
    """A mapping row that also supports SQLite-style numeric indexing."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return tuple(self.values())[key]
        return super().__getitem__(key)


class MyConnection:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, query, params=()):
        query = query.replace("MAX(reported,", "GREATEST(reported,")
        query = query.replace(
            "CAST(strftime('%H',date_attempted) AS INTEGER)",
            "HOUR(date_attempted)",
        )
        query = query.replace("moderation_reason || '; reviewed'", "CONCAT(moderation_reason, '; reviewed')")
        query = query.replace("?", "%s")
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return MyCursor(cursor)

    def commit(self):
        self._connection.commit()

    def close(self):
        self._connection.close()


class MyCursor:
    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = cursor.lastrowid
        self.rowcount = cursor.rowcount

    @staticmethod
    def _row(value):
        if value is None:
            return None
        # MySQL DATETIME columns arrive as Python datetime values; API output
        # and the existing UI expect JSON-friendly timestamp strings.
        return HybridRow({key: str(val) if hasattr(val, "isoformat") else val for key, val in value.items()})

    def fetchone(self):
        return self._row(self._cursor.fetchone())

    def fetchall(self):
        return [self._row(value) for value in self._cursor.fetchall()]


def connect(path=None):
    if not USE_MYSQL:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(path or DB_PATH)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    if USE_MYSQL:
        import pymysql
        from pymysql.cursors import DictCursor

        parsed = urlparse(DATABASE_URL.replace("mysql+pymysql://", "mysql://", 1))
        options = parse_qs(parsed.query)
        ssl_mode = options.get("ssl-mode", options.get("sslmode", ["REQUIRED"]))[0].upper()
        ca_file = os.environ.get("MYSQL_SSL_CA")
        ssl = ({"ca": ca_file, "check_hostname": True} if ca_file else {"check_hostname": False}) if ssl_mode != "DISABLED" else None
        con = pymysql.connect(
            host=parsed.hostname,
            port=parsed.port or 3306,
            user=unquote(parsed.username or ""),
            password=unquote(parsed.password or ""),
            database=(parsed.path or "/").lstrip("/") or "defaultdb",
            charset="utf8mb4",
            connect_timeout=10,
            read_timeout=20,
            write_timeout=20,
            cursorclass=DictCursor,
            autocommit=False,
            ssl=ssl,
        )
        return MyConnection(con)

def initialize_mysql():
    con = connect()
    statements = [
        """CREATE TABLE IF NOT EXISTS users (
          id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, username VARCHAR(20) NOT NULL UNIQUE,
          password_hash VARCHAR(255) NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          daily_streak INTEGER NOT NULL DEFAULT 0, last_daily_date VARCHAR(20), email VARCHAR(320),
          email_verified INTEGER NOT NULL DEFAULT 0, verify_token VARCHAR(128),
          verify_token_expires BIGINT, reset_token VARCHAR(128), reset_token_expires BIGINT,
          chatbot_language VARCHAR(10) NOT NULL DEFAULT 'en', UNIQUE KEY idx_users_email (email)) ENGINE=InnoDB""",
        """CREATE TABLE IF NOT EXISTS attempts (
          id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
          user_id BIGINT NOT NULL, square_order INTEGER NOT NULL, moves_made INTEGER NOT NULL,
          time_taken INTEGER NOT NULL, hints_used INTEGER NOT NULL DEFAULT 0,
          is_daily INTEGER NOT NULL DEFAULT 0, challenge_date VARCHAR(20),
          date_attempted DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          mode VARCHAR(20) NOT NULL DEFAULT 'scramble',
          INDEX idx_attempts_user_id (user_id), INDEX idx_attempts_square_order (square_order),
          INDEX idx_attempts_daily (is_daily, challenge_date, square_order),
          CONSTRAINT fk_attempts_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB""",
        """CREATE TABLE IF NOT EXISTS user_achievements (
          id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, user_id BIGINT NOT NULL,
          achievement_key VARCHAR(100) NOT NULL, earned_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY uq_user_achievement (user_id, achievement_key),
          CONSTRAINT fk_achievements_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB""",
        """CREATE TABLE IF NOT EXISTS game_sessions (
          id VARCHAR(36) PRIMARY KEY, user_id BIGINT NOT NULL, square_order INTEGER NOT NULL,
          solved_grid LONGTEXT NOT NULL, is_daily INTEGER NOT NULL DEFAULT 0,
          challenge_date VARCHAR(20), started_at BIGINT NOT NULL, moves_made INTEGER NOT NULL DEFAULT 0,
          hints_used INTEGER NOT NULL DEFAULT 0, completed_at BIGINT,
          mode VARCHAR(20) NOT NULL DEFAULT 'scramble', attempts_used INTEGER NOT NULL DEFAULT 0,
          INDEX idx_game_user (user_id, square_order),
          CONSTRAINT fk_games_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB""",
        """CREATE TABLE IF NOT EXISTS chatbot_messages (
          id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY, user_id BIGINT NULL,
          request_id VARCHAR(128) NOT NULL, role VARCHAR(20) NOT NULL,
          game_title VARCHAR(255) NOT NULL DEFAULT 'Ramanujan Magic Square', content LONGTEXT NOT NULL,
          context_json LONGTEXT, feedback VARCHAR(30), feedback_note VARCHAR(300),
          reported INTEGER NOT NULL DEFAULT 0, moderation_reason VARCHAR(500),
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_chatbot_user_created (user_id, created_at), INDEX idx_chatbot_request (request_id),
          INDEX idx_chatbot_flagged (reported, moderation_reason),
          CONSTRAINT fk_chatbot_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB""",
    ]
    try:
        for statement in statements:
            con.execute(statement)
        con.commit()
    finally:
        con.close()
