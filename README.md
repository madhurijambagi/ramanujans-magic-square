# SquareVerse

SquareVerse is a Flask and SQLite magic-square puzzle game. Players can solve boards from 3×3 through 10×10, play Daily Challenges, compare leaderboard times, track achievements and export their account history as CSV.

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:3000`. Set `SESSION_SECRET` to a long random value for deployment, and set `ADMIN_USERNAME` before registering the first administrator. To enable the AI chatbot, configure `OPENAI_API_KEY` on the server; `OPENAI_MODEL` defaults to `gpt-4.1-mini`. If the key is absent or OpenAI is unavailable, the chatbot falls back to curated responses. With AI enabled, only the current question, selected reply language, and relevant excerpts from `knowledge/magic-square-guide.md` are sent to OpenAI. Usernames, saved chat history, and live board state are excluded. Account and game data are stored in SQLite under `DATA_DIR` (default: `data/`). The included Render configuration uses a persistent disk mounted at `/var/data`, so the same SQLite database survives code updates and service restarts. Persistent disks require a paid Render web service; Render's free web services have ephemeral filesystems. For another host, point `DATA_DIR` at persistent storage. Do not replace or clear the database when deploying new code.

## Gaming companion

The in-game companion is available on the Play page. It uses OpenAI Responses for retrieval-grounded magic-square and gaming help when configured, with curated responses as a fallback. It supports English and Kannada replies, saved text chat history, player progress summaries, response feedback and an admin review view. Voice chat has been removed. Replies are restricted to MagicSquare and gaming topics. The companion can advise on multiplayer strategy but cannot matchmake or coordinate a live team.

The chatbot's source guide is in `knowledge/`. Add reviewed game guides there to ground future title support.

## Data and deployment

SQLite data is stored in `data/` by default for local use. Set `DATA_DIR` to a persistent location for deployments. A Render blueprint is included in `render.yaml`; it provisions a paid web service and persistent disk. Before moving an existing live deployment to a new disk, copy its existing SQLite database to the disk once, or existing users will need to be migrated into the new database. Deployments that keep the same persistent disk preserve account records; deployments that delete or replace the disk do not.
