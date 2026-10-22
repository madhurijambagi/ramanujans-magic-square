"""Python/Flask backend for Ramanujan's Magic Square.

It intentionally keeps the existing REST URLs and SQLite schema so the
vanilla HTML/CSS/JavaScript frontend can remain unchanged.
"""
import sys
import hashlib
import json
import csv
import difflib
import io
import os
import re
import secrets
import sqlite3
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from chatbot_rules import answer_for, OFF_TOPIC
from chatbot_i18n import kannada_answer, kannada_suggestions

ROOT = Path(__file__).resolve().parent
LOCAL_PACKAGES = ROOT / ".python_packages"
if LOCAL_PACKAGES.exists():
    sys.path.insert(0, str(LOCAL_PACKAGES))
import bcrypt
from flask import Flask, Response, g, jsonify, redirect, request, session, send_from_directory
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "data.sqlite"
ORDERS = [3, 4, 5, 6, 7, 8, 9, 10]
MAX_FILL_ATTEMPTS = 3            # 'Fill the square' mode: checks allowed per round
FILL_RESUME_MS = 30 * 60 * 1000  # an unfinished fill round can be resumed for 30 minutes
CHATBOT_REQUESTS = {}

app = Flask(__name__, static_folder="public", static_url_path="")
app.config.update(SECRET_KEY=os.environ.get("SESSION_SECRET", "magic-square-dev-secret-change-me"), SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    con = g.pop("db", None)
    if con:
        con.close()


def rows(cursor): return [dict(r) for r in cursor.fetchall()]
def row(cursor):
    value = cursor.fetchone()
    return dict(value) if value else None
def error(message, code=400): return jsonify(error=message), code
def now_ms(): return int(time.time() * 1000)
def today(): return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def initialize_database():
    con = sqlite3.connect(DB_PATH)
    con.executescript("""
      PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, is_admin INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );
      CREATE TABLE IF NOT EXISTS attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        square_order INTEGER NOT NULL, moves_made INTEGER NOT NULL,
        time_taken INTEGER NOT NULL, hints_used INTEGER NOT NULL DEFAULT 0,
        is_daily INTEGER NOT NULL DEFAULT 0, challenge_date TEXT,
        date_attempted TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
      );
      CREATE TABLE IF NOT EXISTS user_achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        achievement_key TEXT NOT NULL, earned_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, achievement_key)
      );
      CREATE TABLE IF NOT EXISTS game_sessions (
        id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, square_order INTEGER NOT NULL,
        solved_grid TEXT NOT NULL, is_daily INTEGER NOT NULL DEFAULT 0,
        challenge_date TEXT, started_at INTEGER NOT NULL, moves_made INTEGER NOT NULL DEFAULT 0,
        hints_used INTEGER NOT NULL DEFAULT 0, completed_at INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
      );
      CREATE TABLE IF NOT EXISTS chatbot_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        request_id TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('user','assistant')),
        game_title TEXT NOT NULL DEFAULT 'Ramanujan Magic Square', content TEXT NOT NULL,
        context_json TEXT, feedback TEXT, feedback_note TEXT, reported INTEGER NOT NULL DEFAULT 0,
        moderation_reason TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
      );
    """)
    wanted = {"daily_streak":"INTEGER NOT NULL DEFAULT 0", "last_daily_date":"TEXT", "email":"TEXT", "email_verified":"INTEGER NOT NULL DEFAULT 0", "verify_token":"TEXT", "verify_token_expires":"INTEGER", "reset_token":"TEXT", "reset_token_expires":"INTEGER", "chatbot_language":"TEXT NOT NULL DEFAULT 'en'"}
    present = {r[1] for r in con.execute("PRAGMA table_info(users)")}
    for name, definition in wanted.items():
        if name not in present: con.execute(f"ALTER TABLE users ADD COLUMN {name} {definition}")
    # Fill-in mode: which mode a session/attempt belongs to, and how many checks were used.
    for table, name, definition in [
        ("game_sessions", "mode", "TEXT NOT NULL DEFAULT 'scramble'"),
        ("game_sessions", "attempts_used", "INTEGER NOT NULL DEFAULT 0"),
        ("attempts", "mode", "TEXT NOT NULL DEFAULT 'scramble'"),
    ]:
        cols = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        if name not in cols: con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
    chat_cols={r[1] for r in con.execute("PRAGMA table_info(chatbot_messages)")}
    if "feedback_note" not in chat_cols: con.execute("ALTER TABLE chatbot_messages ADD COLUMN feedback_note TEXT")
    con.executescript("""CREATE INDEX IF NOT EXISTS idx_attempts_user_id ON attempts(user_id);
      CREATE INDEX IF NOT EXISTS idx_attempts_square_order ON attempts(square_order);
      CREATE INDEX IF NOT EXISTS idx_attempts_daily ON attempts(is_daily, challenge_date, square_order);
      CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;""")
    con.executescript("""CREATE INDEX IF NOT EXISTS idx_chatbot_user_created ON chatbot_messages(user_id,created_at);
      CREATE INDEX IF NOT EXISTS idx_chatbot_request ON chatbot_messages(request_id);
      CREATE INDEX IF NOT EXISTS idx_chatbot_flagged ON chatbot_messages(reported,moderation_reason);""")
    con.commit(); con.close()


def auth_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"): return error("Not authenticated.", 401)
        return fn(*args, **kwargs)
    return wrapped


def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        user = row(db().execute("SELECT is_admin FROM users WHERE id=?", (session.get("user_id"),)))
        if not user or not user["is_admin"]: return error("Administrator access required.", 403)
        return fn(*args, **kwargs)
    return wrapped


def constant(n): return n * (n * n + 1) // 2
def order_error(n):
    if n == 2: return "A 2×2 magic square is not mathematically possible."
    if n not in ORDERS: return "Order must be between 2 and 10."
    return None


def daily_progress(uid, date=None):
    """Return the only order a player may play for a given UTC daily run."""
    date = date or today()
    completed = {r[0] for r in db().execute(
        "SELECT square_order FROM attempts WHERE user_id=? AND is_daily=1 AND challenge_date=?",
        (uid, date),
    )}
    next_order = next((order for order in ORDERS if order not in completed), None)
    return date, sorted(completed), next_order


def siamese(n):
    grid = [[0] * n for _ in range(n)]; path = []; r, c = 0, n // 2
    for value in range(1, n * n + 1):
        grid[r][c] = value; path.append({"row":r,"col":c,"value":value})
        nr, nc = (r - 1) % n, (c + 1) % n
        r, c = ((r + 1) % n, c) if grid[nr][nc] else (nr, nc)
    return grid, path


def doubly_even(n):
    grid=[]; path=[]
    for r in range(n):
        line=[]
        for c in range(n):
            value=r*n+c+1; marked=(r%4 == c%4 or r%4+c%4 == 3)
            value=n*n+1-value if marked else value; line.append(value); path.append({"row":r,"col":c,"value":value})
        grid.append(line)
    return grid, path


def singly_even(n):
    m=n//2; base,_=siamese(m); q=m*m; grid=[[0]*n for _ in range(n)]
    for r in range(m):
        for c in range(m):
            v=base[r][c]; grid[r][c]=v; grid[r+m][c]=v+3*q; grid[r][c+m]=v+2*q; grid[r+m][c+m]=v+q
    k=(m-1)//2; middle=m//2
    for r in range(m):
        cols=range(1,k+1) if r == middle else range(k)
        for c in cols: grid[r][c],grid[r+m][c]=grid[r+m][c],grid[r][c]
    for r in range(m):
        for c in range(m-k+1,m): grid[r][c+m],grid[r+m][c+m]=grid[r+m][c+m],grid[r][c+m]
    return grid,[{"row":r,"col":c,"value":grid[r][c]} for r in range(n) for c in range(n)]


def magic_square(n):
    if n % 2: grid,path=siamese(n)
    elif n % 4 == 0: grid,path=doubly_even(n)
    else: grid,path=singly_even(n)
    return [v for line in grid for v in line], path


def seeded_scramble(values, seed_text):
    # Same deterministic goal as the old implementation: one date/order, one puzzle.
    values=list(values); digest=hashlib.sha256(seed_text.encode()).digest(); state=int.from_bytes(digest[:8],"big")
    for i in range(len(values)-1,0,-1):
        state=(state*6364136223846793005+1442695040888963407) & ((1<<64)-1)
        j=state%(i+1); values[i],values[j]=values[j],values[i]
    return values


def validate(values, n, target=None):
    target=target or constant(n)
    if len(values) != n*n: return False
    grid=[values[r*n:(r+1)*n] for r in range(n)]
    return all(sum(line)==target for line in grid) and all(sum(grid[r][c] for r in range(n))==target for c in range(n)) and sum(grid[i][i] for i in range(n))==target and sum(grid[i][n-1-i] for i in range(n))==target


def fill_report(values, n):
    """Grade a fully typed-in grid: number usage first, then every row / column / diagonal."""
    target = constant(n); total = n * n
    grid = [values[r*n:(r+1)*n] for r in range(n)]
    rows_ = [sum(line) for line in grid]
    cols_ = [sum(grid[r][c] for r in range(n)) for c in range(n)]
    diag_main = sum(grid[i][i] for i in range(n)); diag_anti = sum(grid[i][n-1-i] for i in range(n))
    counts = Counter(values)
    out_of_range = sorted({v for v in values if v < 1 or v > total})
    duplicates = sorted(v for v, k in counts.items() if k > 1 and 1 <= v <= total)
    missing = sorted(set(range(1, total + 1)) - set(values))
    problems = []
    if out_of_range: problems.append(f"Use only the numbers 1 to {total}. Not allowed: {', '.join(map(str, out_of_range))}.")
    if duplicates: problems.append(f"Every number can be used only once. Repeated: {', '.join(map(str, duplicates))}.")
    if missing and len(missing) <= 12: problems.append(f"Numbers not used yet: {', '.join(map(str, missing))}.")
    bad_rows = [i + 1 for i, s in enumerate(rows_) if s != target]
    bad_cols = [i + 1 for i, s in enumerate(cols_) if s != target]
    if bad_rows: problems.append(f"Row{'s' if len(bad_rows) > 1 else ''} {', '.join(map(str, bad_rows))} should add up to {target}.")
    if bad_cols: problems.append(f"Column{'s' if len(bad_cols) > 1 else ''} {', '.join(map(str, bad_cols))} should add up to {target}.")
    if diag_main != target: problems.append(f"The main diagonal (top-left to bottom-right) adds up to {diag_main}, not {target}.")
    if diag_anti != target: problems.append(f"The other diagonal (top-right to bottom-left) adds up to {diag_anti}, not {target}.")
    return dict(target=target, rows=rows_, cols=cols_, diag_main=diag_main, diag_anti=diag_anti,
                out_of_range=out_of_range, duplicates=duplicates, missing=missing,
                problems=problems, solved=not problems)


ACHIEVEMENTS=[("first_solve","First Square","Solve your first magic square."),("all_orders","Full Spectrum","Solve at least one square of every order: 3, 4, 5, 6, 7, 8, 9, 10."),("ten_solves","Ten and Counting","Log ten total solve attempts."),("speed_demon","Speed Demon","Solve 3x3 under 20s, 5x5 under 1m, 7x7 under 10m, or 9x9 under 5m."),("no_hints_needed","No Hints Needed","Solve a 7x7 or larger square without using a single hint."),("daily_solver","Daily Devotee","Complete a Daily Challenge square."),("five_solves","Combo Starter","Complete 5 puzzle attempts."),("twenty_five_solves","Puzzle Veteran","Complete 25 puzzle attempts."),("streak_3","Triple Streak","Complete Daily Challenges on 3 consecutive days."),("streak_7","Weeklong Wizard","Complete Daily Challenges on 7 consecutive days."),("hint_free_five","Clean Run","Complete 5 puzzles without using a hint."),("variety_player","Mode Hopper","Complete scramble, fill-in, and at least one Daily Challenge."),("night_owl","Night Owl","Complete a puzzle between 10 PM and 4 AM UTC.")]

def qualifies(key, uid):
    con=db()
    if key=="first_solve": return con.execute("SELECT 1 FROM attempts WHERE user_id=?",(uid,)).fetchone() is not None
    if key=="all_orders": return {r[0] for r in con.execute("SELECT DISTINCT square_order FROM attempts WHERE user_id=?",(uid,))} >= set(ORDERS)
    if key=="ten_solves": return con.execute("SELECT COUNT(*) FROM attempts WHERE user_id=?",(uid,)).fetchone()[0]>=10
    if key=="speed_demon": return con.execute("SELECT 1 FROM attempts WHERE user_id=? AND ((square_order=3 AND time_taken<20) OR (square_order=5 AND time_taken<60) OR (square_order=7 AND time_taken<600) OR (square_order=9 AND time_taken<300))",(uid,)).fetchone() is not None
    if key=="no_hints_needed": return con.execute("SELECT 1 FROM attempts WHERE user_id=? AND square_order>=7 AND hints_used=0",(uid,)).fetchone() is not None
    if key=="daily_solver": return con.execute("SELECT 1 FROM attempts WHERE user_id=? AND is_daily=1",(uid,)).fetchone() is not None
    if key=="five_solves": return con.execute("SELECT COUNT(*) FROM attempts WHERE user_id=?",(uid,)).fetchone()[0]>=5
    if key=="twenty_five_solves": return con.execute("SELECT COUNT(*) FROM attempts WHERE user_id=?",(uid,)).fetchone()[0]>=25
    if key in ("streak_3","streak_7"):
        streak=row(con.execute("SELECT daily_streak FROM users WHERE id=?",(uid,)))
        return bool(streak and streak["daily_streak"] >= (3 if key=="streak_3" else 7))
    if key=="hint_free_five": return con.execute("SELECT COUNT(*) FROM attempts WHERE user_id=? AND hints_used=0",(uid,)).fetchone()[0]>=5
    if key=="variety_player": return {r[0] for r in con.execute("SELECT DISTINCT mode FROM attempts WHERE user_id=?",(uid,))}>={"scramble","fill"} and con.execute("SELECT 1 FROM attempts WHERE user_id=? AND is_daily=1",(uid,)).fetchone() is not None
    if key=="night_owl": return con.execute("SELECT 1 FROM attempts WHERE user_id=? AND CAST(strftime('%H',date_attempted) AS INTEGER)>=22 OR user_id=? AND CAST(strftime('%H',date_attempted) AS INTEGER)<4",(uid,uid)).fetchone() is not None
    return False

def evaluate_achievements(uid):
    con=db(); owned={r[0] for r in con.execute("SELECT achievement_key FROM user_achievements WHERE user_id=?",(uid,))}; new=[]
    for key,_,_ in ACHIEVEMENTS:
        if key not in owned and qualifies(key,uid): con.execute("INSERT INTO user_achievements(user_id,achievement_key) VALUES (?,?)",(uid,key)); new.append(key)
    con.commit(); return new


@app.post("/api/auth/register")
def register():
    data=request.get_json(silent=True) or {}; username=data.get("username",""); password=data.get("password",""); email=(data.get("email") or "").strip().lower() or None
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}",username): return error("Username must be 3-20 characters and contain only letters, numbers, and underscores.")
    if len(password)<8: return error("Password must be at least 8 characters long.")
    if email and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email): return error("That doesn't look like a valid email address.")
    con=db()
    if con.execute("SELECT 1 FROM users WHERE username=?",(username,)).fetchone(): return error("That username is already taken.",409)
    if email and con.execute("SELECT 1 FROM users WHERE email=?",(email,)).fetchone(): return error("That email is already associated with an account.",409)
    is_admin=bool(os.environ.get("ADMIN_USERNAME") == username)
    token=secrets.token_hex(32) if email else None; expiry=now_ms()+86400000 if email else None
    cur=con.execute("INSERT INTO users(username,password_hash,is_admin,email,verify_token,verify_token_expires) VALUES(?,?,?,?,?,?)",(username,bcrypt.hashpw(password.encode(),bcrypt.gensalt()).decode(),int(is_admin),email,token,expiry)); con.commit(); session["user_id"]=cur.lastrowid
    return jsonify(id=cur.lastrowid,username=username,is_admin=is_admin,email=email,email_verified=False),201


@app.post("/api/auth/login")
def login():
    data=request.get_json(silent=True) or {}; user=row(db().execute("SELECT * FROM users WHERE username=?",(data.get("username"),)))
    if not user or not bcrypt.checkpw(str(data.get("password","")).encode(),user["password_hash"].encode()): return error("Invalid username or password.",401)
    session["user_id"]=user["id"]; return jsonify(id=user["id"],username=user["username"],is_admin=bool(user["is_admin"]))


@app.post("/api/auth/logout")
def logout(): session.clear(); return jsonify(ok=True)

@app.post("/api/auth/change-password")
@auth_required
def change_password():
    data=request.get_json(silent=True) or {}; current=str(data.get("current_password", "")); new=str(data.get("new_password", ""))
    if len(new)<8:return error("New password must be at least 8 characters long.")
    user=row(db().execute("SELECT password_hash FROM users WHERE id=?",(session["user_id"],)))
    if not user or not bcrypt.checkpw(current.encode(),user["password_hash"].encode()):return error("Current password is incorrect.",401)
    db().execute("UPDATE users SET password_hash=? WHERE id=?",(bcrypt.hashpw(new.encode(),bcrypt.gensalt()).decode(),session["user_id"]));db().commit();return jsonify(ok=True)

@app.post("/api/auth/email")
@auth_required
def set_email():
    email=str((request.get_json(silent=True) or {}).get("email","")).strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):return error("That doesn't look like a valid email address.")
    duplicate=db().execute("SELECT id FROM users WHERE email=? AND id!=?",(email,session["user_id"])).fetchone()
    if duplicate:return error("That email is already associated with an account.",409)
    db().execute("UPDATE users SET email=?,email_verified=0,verify_token=?,verify_token_expires=? WHERE id=?",(email,secrets.token_hex(32),now_ms()+86400000,session["user_id"]));db().commit();return jsonify(ok=True,email=email)

@app.post("/api/auth/resend-verification")
@auth_required
def resend_verification():
    user=row(db().execute("SELECT email,email_verified FROM users WHERE id=?",(session["user_id"],)))
    if not user or not user["email"]:return error("Add an email address to your profile first.")
    if user["email_verified"]:return jsonify(ok=True,already_verified=True)
    db().execute("UPDATE users SET verify_token=?,verify_token_expires=? WHERE id=?",(secrets.token_hex(32),now_ms()+86400000,session["user_id"]));db().commit();return jsonify(ok=True)

@app.get("/api/auth/export")
@auth_required
def export_account():
    user=row(db().execute("SELECT id,username,email,email_verified,created_at FROM users WHERE id=?",(session["user_id"],)))
    attempts=rows(db().execute("SELECT square_order,moves_made,time_taken,hints_used,is_daily,challenge_date,mode,date_attempted FROM attempts WHERE user_id=? ORDER BY date_attempted",(session["user_id"],)))
    badges=rows(db().execute("SELECT achievement_key,earned_at FROM user_achievements WHERE user_id=? ORDER BY earned_at",(session["user_id"],)))
    chats=rows(db().execute("SELECT role,game_title,content,created_at FROM chatbot_messages WHERE user_id=? ORDER BY id",(session["user_id"],)))
    output=io.StringIO(newline="");writer=csv.writer(output)
    writer.writerow(["record_type","username","email","email_verified","account_created","square_order","moves","time_seconds","hints","daily_challenge","challenge_date","attempt_mode","attempt_date","achievement_key","achievement_earned","chat_role","chat_game","chat_message","chat_date"])
    writer.writerow(["account",user["username"],user["email"] or "",bool(user["email_verified"]),user["created_at"],"","","","","","","","","","","","","",""])
    for attempt in attempts:
        writer.writerow(["attempt",user["username"],user["email"] or "",bool(user["email_verified"]),user["created_at"],attempt["square_order"],attempt["moves_made"],attempt["time_taken"],attempt["hints_used"],bool(attempt["is_daily"]),attempt["challenge_date"] or "",attempt.get("mode") or "scramble",attempt["date_attempted"],"","","","","",""])
    for badge in badges:
        writer.writerow(["achievement",user["username"],"","","","","","","","","","","",badge["achievement_key"],badge["earned_at"],"","","",""])
    for chat in chats:
        writer.writerow(["chat_message",user["username"],"","","","","","","","","","","","","",chat["role"],chat["game_title"],chat["content"],chat["created_at"]])
    return Response("\ufeff"+output.getvalue(),mimetype="text/csv",headers={"Content-Disposition":"attachment; filename=squareverse-account-data.csv"})

@app.delete("/api/auth/account")
@auth_required
def delete_account():
    password=str((request.get_json(silent=True) or {}).get("password", "")); user=row(db().execute("SELECT password_hash FROM users WHERE id=?",(session["user_id"],)))
    if not user or not bcrypt.checkpw(password.encode(),user["password_hash"].encode()):return error("Password is incorrect.",401)
    db().execute("DELETE FROM users WHERE id=?",(session["user_id"],));db().commit();session.clear();return jsonify(ok=True)

@app.post("/api/auth/forgot-password")
def forgot_password():
    # Same neutral response for unknown addresses, as in the Express version.
    data=request.get_json(silent=True) or {}; email=str(data.get("email","")).strip().lower()
    user=row(db().execute("SELECT id FROM users WHERE email=?",(email,)))
    if user:
        token=secrets.token_hex(32); db().execute("UPDATE users SET reset_token=?,reset_token_expires=? WHERE id=?",(token,now_ms()+1800000,user["id"]));db().commit()
        print(f"[mailer development fallback] Reset link: {request.host_url}reset-password.html?token={token}")
    return jsonify(ok=True,message="If that email is associated with an account, a reset link has been sent.")

@app.post("/api/auth/reset-password")
def reset_password():
    data=request.get_json(silent=True) or {}; token=str(data.get("token", "")); new=str(data.get("new_password", ""))
    if not token:return error("Missing reset token.")
    if len(new)<8:return error("New password must be at least 8 characters long.")
    user=row(db().execute("SELECT id,reset_token_expires FROM users WHERE reset_token=?",(token,)))
    if not user or not user["reset_token_expires"] or user["reset_token_expires"]<now_ms():return error("This reset link is invalid or has expired. Request a new one.")
    db().execute("UPDATE users SET password_hash=?,reset_token=NULL,reset_token_expires=NULL WHERE id=?",(bcrypt.hashpw(new.encode(),bcrypt.gensalt()).decode(),user["id"]));db().commit();return jsonify(ok=True)

@app.get("/api/auth/verify-email")
def verify_email():
    token=request.args.get("token",""); user=row(db().execute("SELECT id,verify_token_expires FROM users WHERE verify_token=?",(token,)))
    if not user or not user["verify_token_expires"] or user["verify_token_expires"]<now_ms(): return error("This verification link is invalid or has expired.")
    db().execute("UPDATE users SET email_verified=1,verify_token=NULL,verify_token_expires=NULL WHERE id=?",(user["id"],));db().commit();return redirect("/profile.html?verified=1")

@app.get("/api/auth/me")
@auth_required
def me():
    user=row(db().execute("SELECT id,username,is_admin,created_at,daily_streak,last_daily_date,email,email_verified,chatbot_language FROM users WHERE id=?",(session["user_id"],)))
    user["is_admin"]=bool(user["is_admin"]); user["email_verified"]=bool(user["email_verified"])
    if user.get("chatbot_language") not in ("en", "kn"):
        user["chatbot_language"] = "en"
    return jsonify(user)


@app.post("/api/game/start")
@auth_required
def start_game():
    data=request.get_json(silent=True) or {}; n=data.get("order"); why=order_error(n)
    if why:return error(why)
    mode=data.get("mode","scramble")
    if mode not in ("scramble","fill"):return error("Unknown game mode.")
    daily=bool(data.get("is_daily")); date=today() if daily else None; con=db(); uid=session["user_id"]
    if mode=="fill" and daily:return error("Fill-in mode isn't available for the Daily Challenge.")
    if daily and con.execute("SELECT 1 FROM attempts WHERE user_id=? AND square_order=? AND is_daily=1 AND challenge_date=?",(uid,n,date)).fetchone(): return error("You already completed this daily challenge for this order today.",409)
    if daily:
        _date, _completed, expected = daily_progress(uid, date)
        if expected is None:
            return error("You have completed every Daily Challenge size for today.", 409)
        if n != expected:
            return error(f"Complete the {expected}×{expected} Daily Challenge before playing another size.", 403)
    if mode=="fill":
        active=row(con.execute("SELECT id,started_at,attempts_used FROM game_sessions WHERE user_id=? AND square_order=? AND mode='fill' AND completed_at IS NULL ORDER BY started_at DESC LIMIT 1",(uid,n)))
        if active and now_ms()-active["started_at"]<FILL_RESUME_MS:
            return jsonify(game_id=active["id"],attempts_left=MAX_FILL_ATTEMPTS-active["attempts_used"],elapsed=(now_ms()-active["started_at"])//1000,resumed=True)
        con.execute("UPDATE game_sessions SET completed_at=? WHERE user_id=? AND square_order=? AND mode='fill' AND completed_at IS NULL",(now_ms(),uid,n))
    solved,_=magic_square(n); gid=str(uuid.uuid4()); con.execute("INSERT INTO game_sessions(id,user_id,square_order,solved_grid,is_daily,challenge_date,started_at,mode) VALUES(?,?,?,?,?,?,?,?)",(gid,uid,n,json.dumps(solved),int(daily),date,now_ms(),mode));con.commit()
    if mode=="fill":return jsonify(game_id=gid,attempts_left=MAX_FILL_ATTEMPTS,elapsed=0,resumed=False),201
    return jsonify(game_id=gid),201


@app.get("/api/game/new/<int:n>")
@auth_required
def new_game(n):
    why=order_error(n)
    if why:return error(why)
    solved,path=magic_square(n); import random; scrambled=list(solved); random.SystemRandom().shuffle(scrambled)
    return jsonify(order=n,target=constant(n),solved=solved,path=path,scrambled=scrambled)


@app.get("/api/chatbot/status")
def chatbot_status():
    return jsonify(ai_enabled=False, vision_enabled=False, moderation_enabled=False, model=None,
                   languages=["en", "kn"], games=["Ramanujan's Magic Square"])


def _sanitize_game_context(value):
    if not isinstance(value, dict):
        return {}
    result = {}
    order = value.get("order")
    if type(order) is int and order in ORDERS:
        result["order"] = order
        result["target"] = constant(order)
    for key in ("moves", "hints", "elapsed_seconds"):
        number = value.get(key)
        if type(number) is int:
            result[key] = max(0, min(number, 86400))
    if value.get("mode") in ("scramble", "fill", "daily"):
        result["mode"] = value["mode"]
    if isinstance(value.get("status"), str):
        result["status"] = value["status"][:50]
    grid = value.get("grid")
    if result.get("order") and isinstance(grid, list):
        n = result["order"]
        if len(grid) == n * n and all(type(v) is int and 1 <= v <= n * n for v in grid):
            result["grid"] = [grid[r * n:(r + 1) * n] for r in range(n)]
    return result


def _save_chat_pair(user_id, request_id, game_title, question, answer, context):
    con = db()
    cur = con.execute(
        "INSERT INTO chatbot_messages(user_id,request_id,role,game_title,content,context_json) VALUES(?,?,'user',?,?,?)",
        (user_id, request_id, game_title, question, json.dumps(context, ensure_ascii=False)),
    )
    user_message_id = cur.lastrowid
    cur = con.execute(
        "INSERT INTO chatbot_messages(user_id,request_id,role,game_title,content,context_json) VALUES(?,?,'assistant',?,?,?)",
        (user_id, request_id, game_title, answer, json.dumps(context, ensure_ascii=False)),
    )
    con.commit()
    return user_message_id, cur.lastrowid


def _chat_language_command(text):
    lower = text.lower()
    commandish = any(word in lower for word in ("change", "switch", "set", "reply", "answer", "speak", "talk", "chat", "language", "from now", "ಕನ್ನಡ"))
    if not commandish:
        return None
    if re.search(r"kannada|ಕನ್ನಡ", lower):
        return "kn"
    if re.search(r"english", lower):
        return "en"
    return None


def _autocorrect_chat_text(text):
    """Correct common, low-risk typos without changing the meaning."""
    replacements = {
        "magik":"magic", "mgaic":"magic", "sqaure":"square", "squre":"square",
        "sqare":"square", "constent":"constant", "constat":"constant", "formla":"formula",
        "daliy":"daily", "challange":"challenge", "hinst":"hints", "stategy":"strategy",
        "stratgey":"strategy", "achievment":"achievement", "leaderbord":"leaderboard",
        "logn":"login", "passwrod":"password", "langauge":"language", "kannad":"kannada",
        "engish":"english", "explainn":"explain", "wht":"what", "waht":"what",
        "whta":"what", "hte":"the", "plau":"play", "paly":"play", "wrok":"work",
        "wroking":"working", "scrore":"score",
    }
    vocabulary = set("a about account achievement achievements add after all also an and any are as at available answer app attempt badge badges board build can change chat check challenge column complete constant control correct daily date delete do does download each email english explain fill first formula from game gaming get global grid help hi highest hint hints history how i impossible in install is it leaderboard learn login magic manual many me mode more move multiplayer my number numbers of on or order password play please puzzle row save score scores settings sign size square squares statistics streak strategy sum support target tell that the them there these this time to two undo up use user what when where why with work working you your ramanujan siamese strachey lux doubly".split())
    def replace(match):
        token = match.group(0)
        lower = token.lower()
        fixed = replacements.get(lower)
        if not fixed and len(lower) >= 4 and lower not in vocabulary:
            candidate = difflib.get_close_matches(lower, vocabulary, n=1, cutoff=.92)
            fixed = candidate[0] if candidate and abs(len(candidate[0]) - len(lower)) <= 1 else None
        if not fixed:
            return token
        return fixed.capitalize() if token[:1].isupper() else fixed
    return re.sub(r"[A-Za-z']+", replace, text)


@app.post("/api/chatbot")
def chatbot():
    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "")
    if not isinstance(question, str):
        return error("Question must be text.")
    question = question.strip()
    if not question:
        return error("Ask a question.")
    if len(question) > 500:
        return error("Please keep your question under 500 characters.")
    question = _autocorrect_chat_text(question)

    now = time.time()
    ip = request.remote_addr or "unknown"
    recent = [stamp for stamp in CHATBOT_REQUESTS.get(ip, []) if now - stamp < 60]
    if len(recent) >= 12:
        return error("Chatbot rate limit reached. Please wait a minute and try again.", 429)
    if len(CHATBOT_REQUESTS) > 2048:
        CHATBOT_REQUESTS.clear()
    recent.append(now)
    CHATBOT_REQUESTS[ip] = recent

    user_id = session.get("user_id")
    user = row(db().execute("SELECT username,chatbot_language FROM users WHERE id=?", (user_id,))) if user_id else {}
    saved_language = (user or {}).get("chatbot_language") or "en"
    if saved_language not in ("en", "kn"):
        saved_language = "en"
    requested_language = payload.get("language")
    language = requested_language if requested_language in ("en", "kn") else saved_language
    command_language = _chat_language_command(question)
    if command_language:
        language = command_language
    if user_id:
        db().execute("UPDATE users SET chatbot_language=? WHERE id=?", (language, user_id))
        db().commit()

    game_title = payload.get("game_title", "Ramanujan's Magic Square")
    if not isinstance(game_title, str):
        game_title = "Ramanujan's Magic Square"
    game_title = game_title.strip()[:80] or "Ramanujan's Magic Square"
    game_context = _sanitize_game_context(payload.get("game_context"))
    username = (user or {}).get("username") or "there"
    request_id = str(uuid.uuid4())

    if command_language:
        answer = ("I'll reply in English from now on." if language == "en"
                  else "ಸರಿ, ಇನ್ನು ಮುಂದೆ ನಾನು ಕನ್ನಡದಲ್ಲೇ ಉತ್ತರಿಸುತ್ತೇನೆ.")
        suggestions = []
        in_scope = True
    else:
        answer, suggestions, in_scope = answer_for(question, username, game_context)
        if in_scope and game_context.get("grid") and re.search(r"current board|my board|which rows|which columns|what is happening on (?:the )?board|explain (?:the )?board", question, re.I):
            grid = game_context["grid"]
            n = game_context["order"]
            target = constant(n)
            lines = [(f"row {i + 1}", sum(line)) for i, line in enumerate(grid)]
            lines += [(f"column {c + 1}", sum(grid[r][c] for r in range(n))) for c in range(n)]
            lines += [("main diagonal", sum(grid[i][i] for i in range(n))), ("other diagonal", sum(grid[i][n - i - 1] for i in range(n)))]
            correct = [name for name, total in lines if total == target]
            answer = f"Your {n}×{n} board has target {target}. Correct lines: {', '.join(correct) if correct else 'none yet'}. Check the sum labels for the lines that need work."
    if not in_scope:
        answer = OFF_TOPIC
        suggestions = []

    # Curated answers remain the single source of game knowledge; render them
    # in Kannada when that reply language is selected, including voice replies.
    if language == "kn":
        answer = kannada_answer(question, answer, username)
        suggestions = kannada_suggestions(suggestions)

    uid, aid = _save_chat_pair(
        user_id, request_id, game_title, question, answer,
        {"game": game_context, "language": language, "rule_based": True},
    )
    return jsonify(answer=answer, ai=False, language=language, speech_language=language,
                   suggestions=suggestions, user_message_id=uid, assistant_message_id=aid)

@app.get("/api/chatbot/history")
@auth_required
def chatbot_history():
    return jsonify(rows(db().execute("SELECT id,role,game_title,content,feedback,reported,created_at FROM chatbot_messages WHERE user_id=? ORDER BY id DESC LIMIT 60",(session["user_id"],)))[::-1])


@app.delete("/api/chatbot/history")
@auth_required
def clear_chatbot_history():
    db().execute("DELETE FROM chatbot_messages WHERE user_id=?",(session["user_id"],)); db().commit(); return jsonify(ok=True)


@app.post("/api/chatbot/feedback")
@auth_required
def chatbot_feedback():
    payload=request.get_json(silent=True) or {}; message_id=payload.get("message_id"); rating=payload.get("rating"); note=payload.get("note","")
    if type(message_id) is not int or rating not in ("helpful","unhelpful","report"): return error("Choose helpful, unhelpful, or report feedback.")
    if not isinstance(note,str) or len(note)>300: return error("Feedback notes must be 300 characters or fewer.")
    flagged=int(rating=="report")
    cur=db().execute("UPDATE chatbot_messages SET feedback=?,feedback_note=?,reported=MAX(reported,?) WHERE id=? AND user_id=? AND role='assistant'",(rating,note.strip(),flagged,message_id,session["user_id"]))
    if not cur.rowcount: return error("Chat response not found.",404)
    db().commit(); return jsonify(ok=True)


@app.get("/api/admin/chatbot")
@admin_required
def admin_chatbot_review():
    con=db()
    totals=row(con.execute("SELECT COUNT(*) AS messages, SUM(CASE WHEN reported=1 THEN 1 ELSE 0 END) AS reports, SUM(CASE WHEN feedback='unhelpful' THEN 1 ELSE 0 END) AS unhelpful FROM chatbot_messages WHERE role='assistant'")) or {}
    items=rows(con.execute("""SELECT a.id,a.request_id,a.game_title,a.content,a.feedback,a.feedback_note,a.reported,a.moderation_reason,a.created_at,
      u.username, (SELECT content FROM chatbot_messages q WHERE q.request_id=a.request_id AND q.role='user' ORDER BY q.id LIMIT 1) AS question
      FROM chatbot_messages a LEFT JOIN users u ON u.id=a.user_id WHERE a.role='assistant'
      ORDER BY a.reported DESC,a.id DESC LIMIT 100"""))
    return jsonify(summary=totals,messages=items)


@app.patch("/api/admin/chatbot/<int:message_id>/resolve")
@admin_required
def admin_resolve_chatbot_report(message_id):
    cur=db().execute("UPDATE chatbot_messages SET reported=0,moderation_reason=CASE WHEN moderation_reason IS NULL THEN 'reviewed' ELSE moderation_reason || '; reviewed' END WHERE id=? AND role='assistant'",(message_id,))
    if not cur.rowcount:return error("Chat response not found.",404)
    db().commit();return jsonify(ok=True)

@app.post("/api/game/check")
@auth_required
def check_fill():
    """Fill-in mode: grade the student's grid. Every complete grid costs one of the 3 attempts (counted on the server)."""
    data=request.get_json(silent=True) or {}; con=db(); uid=session["user_id"]
    game=row(con.execute("SELECT * FROM game_sessions WHERE id=? AND user_id=?",(data.get("game_id"),uid)))
    if not game or game["completed_at"] or game["mode"]!="fill":return error("This game session is not available.")
    n=game["square_order"]; values=data.get("grid")
    if not isinstance(values,list) or len(values)!=n*n or any(type(v) is not int for v in values):return error("Send one whole number for every cell.")
    if any(v==0 for v in values):return error("Fill every cell before checking. An incomplete grid does not use up an attempt.")
    cur=con.execute("UPDATE game_sessions SET attempts_used=attempts_used+1 WHERE id=? AND completed_at IS NULL AND attempts_used<?",(game["id"],MAX_FILL_ATTEMPTS))
    if not cur.rowcount:return error("No attempts left for this round.",409)
    used=game["attempts_used"]+1; left=MAX_FILL_ATTEMPTS-used; report=fill_report(values,n)
    result=dict(report,attempts_used=used,attempts_left=left,finished=report["solved"] or left<=0)
    if report["solved"]:
        elapsed=max(1,(now_ms()-game["started_at"])//1000)
        con.execute("INSERT INTO attempts(user_id,square_order,moves_made,time_taken,hints_used,is_daily,challenge_date,mode) VALUES(?,?,?,?,0,0,NULL,'fill')",(uid,n,used,elapsed))
        con.execute("UPDATE game_sessions SET completed_at=? WHERE id=?",(now_ms(),game["id"]));con.commit()
        result.update(time_taken=elapsed,newly_earned=evaluate_achievements(uid))
    elif left<=0:
        con.execute("UPDATE game_sessions SET completed_at=? WHERE id=?",(now_ms(),game["id"]));con.commit()
        result.update(solution=json.loads(game["solved_grid"]))
    else:con.commit()
    return jsonify(result)


@app.post("/api/attempts/progress")
@auth_required
def progress():
    data=request.get_json(silent=True) or {}; column={"move":"moves_made","hint":"hints_used"}.get(data.get("action"))
    if not column:return error("Invalid progress update.")
    cur=db().execute(f"UPDATE game_sessions SET {column}={column}+1 WHERE id=? AND user_id=? AND completed_at IS NULL",(data.get("game_id"),session["user_id"]));db().commit()
    return jsonify(ok=True) if cur.rowcount else error("Game session is not active.")


@app.post("/api/attempts")
@auth_required
def submit_attempt():
    data=request.get_json(silent=True) or {}; con=db(); game=row(con.execute("SELECT * FROM game_sessions WHERE id=? AND user_id=?",(data.get("game_id"),session["user_id"])))
    if not game or game["completed_at"] or game["mode"]!="scramble":return error("This game session is not available.")
    solved=json.loads(game["solved_grid"]); candidate=data.get("grid",[])
    if candidate != solved or not validate(candidate,game["square_order"]):return error("The submitted grid is not the solved puzzle.")
    if game["is_daily"] and con.execute("SELECT 1 FROM attempts WHERE user_id=? AND square_order=? AND is_daily=1 AND challenge_date=?",(session["user_id"],game["square_order"],game["challenge_date"])).fetchone():return error("You already completed this daily challenge for this order today.",409)
    elapsed=max(1,(now_ms()-game["started_at"])//1000); cur=con.execute("INSERT INTO attempts(user_id,square_order,moves_made,time_taken,hints_used,is_daily,challenge_date) VALUES(?,?,?,?,?,?,?)",(session["user_id"],game["square_order"],game["moves_made"],elapsed,game["hints_used"],game["is_daily"],game["challenge_date"]));con.execute("UPDATE game_sessions SET completed_at=? WHERE id=?",(now_ms(),game["id"]));con.commit()
    if game["is_daily"]:
        user=row(con.execute("SELECT daily_streak,last_daily_date FROM users WHERE id=?",(session["user_id"],)))
        if user["last_daily_date"] != game["challenge_date"]:
            previous=datetime.fromisoformat(user["last_daily_date"]).date() if user["last_daily_date"] else None
            gap=(datetime.fromisoformat(game["challenge_date"]).date()-previous).days if previous else 1
            streak=max(0,user["daily_streak"]-(gap-1)) if gap>1 else user["daily_streak"]
            con.execute("UPDATE users SET daily_streak=?,last_daily_date=? WHERE id=?",(streak+1,game["challenge_date"],session["user_id"]));con.commit()
    return jsonify(id=cur.lastrowid,newly_earned=evaluate_achievements(session["user_id"])),201


@app.get("/api/attempts/history")
@auth_required
def history(): return jsonify(rows(db().execute("SELECT id,square_order,moves_made,time_taken,hints_used,is_daily,challenge_date,mode,date_attempted FROM attempts WHERE user_id=? ORDER BY date_attempted DESC",(session["user_id"],))))
@app.get("/api/attempts/best")
@auth_required
def best(): return jsonify({str(r["square_order"]):r["best_time"] for r in rows(db().execute("SELECT square_order,MIN(time_taken) best_time FROM attempts WHERE user_id=? GROUP BY square_order",(session["user_id"],)))})


@app.get("/api/daily/<int:n>")
@auth_required
def daily(n):
    why=order_error(n)
    if why:return error(why)
    date, completed, expected = daily_progress(session["user_id"])
    if expected is None:
        return error("You have completed every Daily Challenge size for today.", 409)
    if n != expected:
        return error(f"Complete the {expected}×{expected} Daily Challenge before playing another size.", 403)
    solved,path=magic_square(n); attempted=row(db().execute("SELECT time_taken,moves_made,hints_used FROM attempts WHERE user_id=? AND square_order=? AND is_daily=1 AND challenge_date=?",(session["user_id"],n,date)))
    return jsonify(date=date,order=n,target=constant(n),solved=solved,path=path,scrambled=seeded_scramble(solved,f"{date}:{n}"),already_attempted=bool(attempted),result=attempted)


@app.get("/api/daily/progress")
@auth_required
def daily_sequence_progress():
    date, completed, next_order = daily_progress(session["user_id"])
    return jsonify(date=date, completed_orders=completed, next_order=next_order, complete=next_order is None)


@app.get("/api/leaderboard/<int:n>")
def leaderboard(n):
    if n not in ORDERS:return error("Invalid square order.")
    return jsonify(rows(db().execute("SELECT u.username,a.time_taken,a.moves_made,a.date_attempted FROM attempts a JOIN users u ON u.id=a.user_id WHERE a.square_order=? AND a.mode='scramble' ORDER BY a.time_taken,a.moves_made LIMIT 20",(n,))))
@app.get("/api/leaderboard/daily/<int:n>")
def daily_leaderboard(n):
    if n not in ORDERS:return error("Invalid square order.")
    return jsonify(rows(db().execute("SELECT u.username,a.time_taken,a.moves_made,a.hints_used,a.date_attempted FROM attempts a JOIN users u ON u.id=a.user_id WHERE a.square_order=? AND a.is_daily=1 AND a.challenge_date=? ORDER BY a.time_taken,a.moves_made LIMIT 20",(n,today()))))


@app.get("/api/achievements/mine")
@auth_required
def achievements():
    evaluate_achievements(session["user_id"])
    earned={r["achievement_key"]:r["earned_at"] for r in rows(db().execute("SELECT achievement_key,earned_at FROM user_achievements WHERE user_id=?",(session["user_id"],)))}
    return jsonify([{"key":k,"name":n,"description":d,"earned":k in earned,"earned_at":earned.get(k)} for k,n,d in ACHIEVEMENTS])


@app.get("/api/ramanujan/<int:a>/<int:b>/<int:c>/<int:d>")
def ramanujan(a,b,c,d):
    grid=[[a,b,c,d],[d+1,c-1,b-3,a+3],[b-2,a+2,d+2,c-2],[c+1,d-1,a+1,b-1]]; shift=max(0,1-min(v for line in grid for v in line)); grid=[[v+shift for v in line] for line in grid]; flat=[v for line in grid for v in line]; target=a+b+c+d+4*shift
    return jsonify(grid=grid,flat=flat,target=target,distinct=len(set(flat))==16,valid=validate(flat,4,target),allNatural=all(v>=1 for v in flat),shift=shift)


@app.get("/api/admin/users")
@admin_required
def admin_users(): return jsonify(rows(db().execute("SELECT u.id,u.username,u.is_admin,u.created_at,COUNT(a.id) attempt_count FROM users u LEFT JOIN attempts a ON a.user_id=u.id GROUP BY u.id ORDER BY u.created_at")))
@app.get("/api/admin/attempts")
@admin_required
def admin_attempts(): return jsonify(rows(db().execute("SELECT a.id,a.square_order,a.moves_made,a.time_taken,a.date_attempted,u.username,u.id user_id FROM attempts a JOIN users u ON u.id=a.user_id ORDER BY a.date_attempted DESC LIMIT 200")))
@app.patch("/api/admin/users/<int:uid>/role")
@admin_required
def role(uid):
    flag=(request.get_json(silent=True) or {}).get("is_admin")
    if not isinstance(flag,bool):return error("is_admin (boolean) is required.")
    if not row(db().execute("SELECT id FROM users WHERE id=?",(uid,))):return error("User not found.",404)
    if not flag and db().execute("SELECT COUNT(*) FROM users WHERE is_admin=1").fetchone()[0]<=1:return error("Can't remove the last remaining administrator.")
    db().execute("UPDATE users SET is_admin=? WHERE id=?",(int(flag),uid));db().commit();return jsonify(ok=True,id=uid,is_admin=flag)
@app.delete("/api/admin/attempts/<int:aid>")
@admin_required
def delete_attempt(aid):
    cur=db().execute("DELETE FROM attempts WHERE id=?",(aid,));db().commit();return jsonify(ok=True) if cur.rowcount else error("Attempt not found.",404)


@app.get("/")
def index(): return send_from_directory(ROOT/"public","index.html")
@app.get("/<path:filename>")
def static_files(filename): return send_from_directory(ROOT/"public",filename)


initialize_database()

if __name__ == "__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",3000)))

