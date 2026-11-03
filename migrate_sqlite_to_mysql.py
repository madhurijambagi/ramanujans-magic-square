"""Copy all local SQLite account/game records into an empty MySQL database."""
import os
import sqlite3
import sys
from getpass import getpass
from pathlib import Path

TABLES = ("users", "attempts", "user_achievements", "game_sessions", "chatbot_messages")


def main():
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        url = getpass("Paste the MySQL connection URL (input hidden): ").strip()
    if not url.startswith(("mysql://", "mysql+pymysql://")):
        raise SystemExit("A MySQL URL beginning with mysql:// is required.")
    os.environ["DATABASE_URL"] = url

    from database import connect, initialize_mysql

    source_path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/data.sqlite").resolve()
    if not source_path.is_file():
        raise SystemExit(f"SQLite source database not found: {source_path}")

    initialize_mysql()
    source = sqlite3.connect(f"{source_path.as_uri()}?mode=ro", uri=True)
    source.row_factory = sqlite3.Row
    destination = connect()
    imported = {}
    try:
        for table in TABLES:
            count = destination.execute(f"SELECT COUNT(*) AS count FROM `{table}`").fetchone()["count"]
            if count:
                raise SystemExit(
                    f"MySQL table {table!r} already has {count} rows; migration stopped without importing."
                )

        for table in TABLES:
            source_columns = [r[1] for r in source.execute(f"PRAGMA table_info({table})")]
            target_columns = {
                row["Field"] for row in destination.execute(f"SHOW COLUMNS FROM `{table}`").fetchall()
            }
            columns = [name for name in source_columns if name in target_columns]
            quoted_columns = ", ".join(f"`{name}`" for name in columns)
            placeholders = ", ".join("%s" for _ in columns)
            insert = f"INSERT INTO `{table}` ({quoted_columns}) VALUES ({placeholders})"
            select = f"SELECT {quoted_columns} FROM `{table}` ORDER BY rowid"
            source_rows = source.execute(select).fetchall()
            for row in source_rows:
                destination.execute(insert, tuple(row[name] for name in columns))
            imported[table] = len(source_rows)

        destination.commit()
        for table, count in imported.items():
            print(f"{table}: {count} rows copied")
        print("Migration complete. MySQL now contains the SQLite records.")
    except Exception:
        destination._connection.rollback()
        raise
    finally:
        source.close()
        destination.close()


if __name__ == "__main__":
    main()
