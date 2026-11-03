"""Copy all local SQLite account/game data into an initialized PostgreSQL DB.

Run once with DATABASE_URL set, after creating the PostgreSQL database:
    python migrate_sqlite_to_postgres.py [path/to/data.sqlite]

The destination must be empty. This guard prevents overwriting registrations or
history already written to PostgreSQL.
"""
import os
import sqlite3
import sys
from getpass import getpass
from pathlib import Path

import psycopg
from psycopg import sql

TABLES = ("users", "attempts", "user_achievements", "game_sessions", "chatbot_messages")


def main():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        url = getpass("Paste the PostgreSQL connection URL (input hidden): ").strip()
    if not url.startswith(("postgres://", "postgresql://")):
        raise SystemExit("A PostgreSQL URL beginning with postgres:// or postgresql:// is required.")
    os.environ["DATABASE_URL"] = url
    from database import initialize_postgres

    source_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/data.sqlite").resolve()
    if not source_path.is_file():
        raise SystemExit(f"SQLite source database not found: {source_path}")

    initialize_postgres()
    source = sqlite3.connect(f"{source_path.as_uri()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    destination = psycopg.connect(url, sslmode=os.environ.get("DB_SSLMODE", "require"))
    try:
        with destination.transaction():
            for table in TABLES:
                count = destination.execute(
                    sql.SQL("SELECT COUNT(*) FROM {} ").format(sql.Identifier(table))
                ).fetchone()[0]
                if count:
                    raise SystemExit(
                        f"PostgreSQL table {table!r} already has {count} rows; "
                        "migration stopped without changing anything."
                    )

            imported = {}
            for table in TABLES:
                source_columns = [r[1] for r in source.execute(f"PRAGMA table_info({table})")]
                target_columns = {
                    row[0] for row in destination.execute(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema='public' AND table_name=%s", (table,)
                    ).fetchall()
                }
                columns = [name for name in source_columns if name in target_columns]
                if not columns:
                    continue
                quoted = sql.SQL(", ").join(map(sql.Identifier, columns))
                insert = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table), quoted,
                    sql.SQL(", ").join(sql.Placeholder() for _ in columns),
                )
                source_rows = source.execute(
                    sql.SQL("SELECT {} FROM {} ORDER BY rowid").format(
                        sql.SQL(", ").join(map(sql.Identifier, columns)), sql.Identifier(table)
                    ).as_string(destination)
                ).fetchall()
                for row in source_rows:
                    destination.execute(insert, tuple(row[name] for name in columns))
                imported[table] = len(source_rows)

            for table in ("users", "attempts", "user_achievements", "chatbot_messages"):
                destination.execute(
                    "SELECT setval(pg_get_serial_sequence(%s, 'id'), "
                    "GREATEST(COALESCE(MAX(id), 1), 1), COUNT(*) > 0) FROM "
                    + table,
                    (table,),
                )
        for table, count in imported.items():
            print(f"{table}: {count} rows copied")
        print("Migration complete. PostgreSQL now contains the SQLite records.")
    finally:
        source.close()
        destination.close()


if __name__ == "__main__":
    main()
