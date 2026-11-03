# SquareVerse

SquareVerse is a Flask magic-square puzzle game. Players can solve boards from 3×3 through 10×10, play Daily Challenges, compare leaderboard times, track achievements and export their account history as CSV. Local development uses SQLite; production can use PostgreSQL through `DATABASE_URL`.

See [System Workflow](SYSTEM_WORKFLOW.md) for the application architecture and the main player, persistence, and chatbot flows.

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:3000`. Without `DATABASE_URL`, local runs use SQLite at `data/data.sqlite`. Set `SESSION_SECRET` to a long random value for deployment, and set `ADMIN_USERNAME` before registering the first administrator. To enable the AI chatbot, configure `OPENAI_API_KEY` on the server; `OPENAI_MODEL` defaults to `gpt-4.1-mini`. If the key is absent or OpenAI is unavailable, the chatbot falls back to curated responses. With AI enabled, only the current question, selected reply language, and relevant excerpts from `knowledge/magic-square-guide.md` are sent to OpenAI. Usernames, saved chat history, and live board state are excluded. When `DATABASE_URL` is a PostgreSQL connection URL, accounts and all game history are stored in PostgreSQL and survive Render restarts and redeploys. Keep `SESSION_SECRET` stable across deploys so signed login sessions remain valid.

## Gaming companion

The in-game companion is available on the Play page. It uses OpenAI Responses for retrieval-grounded magic-square and gaming help when configured, with curated responses as a fallback. It supports English and Kannada replies, saved text chat history, player progress summaries, response feedback and an admin review view. Voice chat has been removed. Replies are restricted to MagicSquare and gaming topics. The companion can advise on multiplayer strategy but cannot matchmake or coordinate a live team.

The chatbot's source guide is in `knowledge/`. Add reviewed game guides there to ground future title support.

## Data and deployment

The Render Blueprint defines both the Free web service and a Free Render Postgres database, connected through `DATABASE_URL`. Free Render Postgres has 1 GB storage, expires 30 days after creation, and has no backups; it can be upgraded during a 14-day grace period after expiration. Keep a separate backup and plan for the database's expiration. To copy existing SQLite accounts and history, run `python migrate_sqlite_to_postgres.py [path/to/data.sqlite]` locally and enter the database's external URL when prompted; the destination must be empty. Render should use the database's internal URL. Never commit a database URL or SQLite database containing account data.
