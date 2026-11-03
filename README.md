# SquareVerse

SquareVerse is a Flask magic-square puzzle game. Players can solve boards from 3×3 through 10×10, play Daily Challenges, compare leaderboard times, track achievements and export their account history as CSV. Local development uses SQLite; production can use MySQL through `DATABASE_URL`.

See [System Workflow](SYSTEM_WORKFLOW.md) for the application architecture and the main player, persistence, and chatbot flows.

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:3000`. Without `DATABASE_URL`, local runs use SQLite at `data/data.sqlite`. Set `SESSION_SECRET` to a long random value for deployment, and set `ADMIN_USERNAME` before registering the first administrator. To enable the AI chatbot, configure `OPENAI_API_KEY` on the server; `OPENAI_MODEL` defaults to `gpt-4.1-mini`. If the key is absent or OpenAI is unavailable, the chatbot falls back to curated responses. With AI enabled, only the current question, selected reply language, and relevant excerpts from `knowledge/magic-square-guide.md` are sent to OpenAI. Usernames, saved chat history, and live board state are excluded. When `DATABASE_URL` is a MySQL connection URL, accounts and all game history are stored in MySQL and survive Render restarts and redeploys. Keep `SESSION_SECRET` stable across deploys so signed login sessions remain valid.

## Gaming companion

The in-game companion is available on the Play page. It uses OpenAI Responses for retrieval-grounded magic-square and gaming help when configured, with curated responses as a fallback. It supports English and Kannada replies, saved text chat history, player progress summaries, response feedback and an admin review view. Voice chat has been removed. Replies are restricted to MagicSquare and gaming topics. The companion can advise on multiplayer strategy but cannot matchmake or coordinate a live team.

The chatbot's source guide is in `knowledge/`. Add reviewed game guides there to ground future title support.

## Data and deployment

For a free Render web service, create an external MySQL database and add its service URL as the `DATABASE_URL` environment variable. The included `render.yaml` keeps the web service on Render's Free plan and prompts for this secret. Aiven currently offers a free MySQL service with 1 GB storage and backups; it may power off after inactivity, but can be powered back on. Check current provider limits and keep a separate backup. Copy existing SQLite accounts and history once with `python migrate_sqlite_to_mysql.py [path/to/data.sqlite]`; the destination must be empty. Never commit a database URL or SQLite database containing account data.
