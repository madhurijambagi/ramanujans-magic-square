const path = require("path");
const fs = require("fs");
const Database = require("better-sqlite3");

// A managed host can mount durable storage outside the application directory.
// Keep the local `data` directory as the development default.
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, "..", "data");
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

const DB_PATH = path.join(DATA_DIR, "data.sqlite");
const db = new Database(DB_PATH);

// Reliability: WAL mode + foreign key enforcement
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
  );

  CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    square_order INTEGER NOT NULL,
    moves_made INTEGER NOT NULL,
    time_taken INTEGER NOT NULL,
    hints_used INTEGER NOT NULL DEFAULT 0,
    is_daily INTEGER NOT NULL DEFAULT 0,
    challenge_date TEXT,
    date_attempted TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  );

  CREATE TABLE IF NOT EXISTS user_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    achievement_key TEXT NOT NULL,
    earned_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, achievement_key)
  );

  CREATE TABLE IF NOT EXISTS game_sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    square_order INTEGER NOT NULL,
    solved_grid TEXT NOT NULL,
    is_daily INTEGER NOT NULL DEFAULT 0,
    challenge_date TEXT,
    started_at INTEGER NOT NULL,
    moves_made INTEGER NOT NULL DEFAULT 0,
    hints_used INTEGER NOT NULL DEFAULT 0,
    completed_at INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  );
`);

// --- Lightweight migration guard for pre-existing databases created before
//     the hints/daily-challenge/achievements features were added. This must
//     run BEFORE any index touches these columns, since CREATE TABLE IF NOT
//     EXISTS is a no-op on a database that already has an `attempts` table
//     from the earlier schema (it won't retroactively add new columns). ---
const attemptCols = db.prepare("PRAGMA table_info(attempts)").all().map((c) => c.name);
if (!attemptCols.includes("hints_used")) {
  db.exec("ALTER TABLE attempts ADD COLUMN hints_used INTEGER NOT NULL DEFAULT 0");
}
if (!attemptCols.includes("is_daily")) {
  db.exec("ALTER TABLE attempts ADD COLUMN is_daily INTEGER NOT NULL DEFAULT 0");
}
if (!attemptCols.includes("challenge_date")) {
  db.exec("ALTER TABLE attempts ADD COLUMN challenge_date TEXT");
}

// Indexes are created only after the columns above are guaranteed to exist.
db.exec(`
  CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id);
  CREATE INDEX IF NOT EXISTS idx_attempts_square_order ON attempts(square_order);
  CREATE INDEX IF NOT EXISTS idx_attempts_daily ON attempts(is_daily, challenge_date, square_order);
`);

const userCols = db.prepare("PRAGMA table_info(users)").all().map((c) => c.name);
if (!userCols.includes("daily_streak")) db.exec("ALTER TABLE users ADD COLUMN daily_streak INTEGER NOT NULL DEFAULT 0");
if (!userCols.includes("last_daily_date")) db.exec("ALTER TABLE users ADD COLUMN last_daily_date TEXT");

// --- Account management: optional email, verification, and password reset ---
if (!userCols.includes("email")) db.exec("ALTER TABLE users ADD COLUMN email TEXT");
if (!userCols.includes("email_verified")) db.exec("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0");
if (!userCols.includes("verify_token")) db.exec("ALTER TABLE users ADD COLUMN verify_token TEXT");
if (!userCols.includes("verify_token_expires")) db.exec("ALTER TABLE users ADD COLUMN verify_token_expires INTEGER");
if (!userCols.includes("reset_token")) db.exec("ALTER TABLE users ADD COLUMN reset_token TEXT");
if (!userCols.includes("reset_token_expires")) db.exec("ALTER TABLE users ADD COLUMN reset_token_expires INTEGER");

db.exec(`CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;`);

module.exports = db;
