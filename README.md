# SquareVerse

SquareVerse is a Flask and SQLite magic-square puzzle game. Players can solve boards from 3×3 through 10×10, play Daily Challenges, compare leaderboard times, track achievements and export their account history as CSV.

## Run locally

```powershell
python -m pip install -r requirements.txt
python app.py
```

Open `http://localhost:3000`. Set `SESSION_SECRET` for deployment. Set `ADMIN_USERNAME` before registering the first administrator. Optional `OPENAI_API_KEY` enables AI chat, screenshot understanding and model-based moderation; `OPENAI_MODEL` can select the model. Never expose this key in browser code.

## Gaming companion

The in-game companion is available on the Play page. It provides magic-square and gaming help, puzzle context, multilingual replies, browser voice interaction, screenshot analysis when configured, saved chat history, player progress summaries, response feedback and an admin review view. Without an AI key, deterministic magic-square help, grid checks, and progress summaries remain available. Replies are restricted to MagicSquare and gaming topics. The companion can advise on multiplayer strategy but cannot matchmake or coordinate a live team.

The chatbot's source guide is in `knowledge/`. Add reviewed game guides there to ground future title support.

## Data and deployment

SQLite data is stored in `data/` by default. Set `DATA_DIR` to use another persistent location. A Render blueprint is included in `render.yaml`; deploy it from a connected hosting account and configure the environment secrets there.
