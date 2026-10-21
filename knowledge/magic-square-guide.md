# SquareVerse: Ramanujan's Magic Square

## Game rules
The game creates normal magic squares for orders 3 through 10 using 1 through n² once. Every row, column, and both main diagonals must total M(n) = n(n² + 1) / 2. The 2×2 normal magic square is impossible.

## Modes and controls
In Swap Puzzle mode, select two tiles to swap them until the displayed construction is restored. Undo reverses the last swap. Hint points to one useful swap and adds 15 seconds. In Fill the Square mode, enter numbers in an empty grid; there are three checks. The Daily Challenge is a shared daily puzzle and contributes to the player's streak.

## Construction methods
Odd orders use the Siamese method. Orders divisible by four use the complement pattern. Singly-even orders use the Strachey construction. The server generates and validates the target grid; client-sent solve times are not trusted.

## Strategies
Start with the target sum. Compare completed rows and columns with it. In swap mode, use the sum labels to see which lines are already correct, and prefer swaps that improve more than one line. A hint is available when stuck, with a time penalty.

## Progress
The player dashboard tracks solve times, moves, hints, daily streaks, and achievements. The gaming companion can give multiplayer strategy advice, but live matchmaking and teammate coordination require a separate game-platform integration.

## Technical support
The app is a Flask server with a SQLite database. Run `python -m pip install -r requirements.txt`, then `python app.py` and open `http://localhost:3000`. Set `SESSION_SECRET` for a deployment. OpenAI-powered chatbot replies and screenshot analysis require `OPENAI_API_KEY` in the server environment. Keep that key out of browser code and the repository.

## SquareVerse FAQ
A magic square uses each integer from 1 through n² exactly once. Every row, column, and both main diagonals add to the magic constant n(n²+1)/2. Orders 3 through 10 are playable; a normal 2×2 magic square cannot meet the constraints with four distinct values.

## Ramanujan's date square
The Formula page can construct a 4×4 date-of-birth square from the entered date. It is a personalized construction inspired by Ramanujan's famous birthday square; explain what the page computes without claiming the player's date is stored unless the app confirms that.

## Modes and features FAQ
Swap Puzzle mode starts from a scrambled valid target and asks the player to restore it by swapping tiles. Undo reverses the last swap. Fill the Square mode starts with blank cells, accepts values, and permits three checks per round. Manual mode lets players enter values and inspect whether the constraints are satisfied. The Daily Challenge is shared by players for the day; completed daily puzzles contribute to streaks.

Hints identify one useful swap and add 15 seconds to the timer. The dashboard shows completed attempts, size, time, moves, hints, streaks, and earned achievements. Badges unlock when their displayed criteria are met. The leaderboard compares completed eligible attempts using the application's scoring rules; do not invent hidden tie-break rules.

## Construction FAQ
The Siamese method constructs odd-order squares by moving up and right with wraparound, moving down when the next cell is occupied. Doubly-even orders use the complement pattern. Singly-even orders use Strachey/LUX-style constructions. Use the exact method names above and avoid asserting that one construction applies to every order.

## Account and installation FAQ
Players can sign in to save attempts and achievements, use Profile to manage account settings, and use the dashboard to inspect progress. For local development, install Python dependencies from `requirements.txt`, run `python app.py`, and browse to `http://localhost:3000`. For deployed AI replies and screenshot analysis, configure `OPENAI_API_KEY` on the server and use a strong `SESSION_SECRET`. Never ask a player to post passwords, API keys, or private credentials in chat.

## Scope and screenshot guidance
Answer questions about this MagicSquare site, its puzzle rules and modes, game strategy, progress features, and gaming support. Decline unrelated requests. The current chat widget does not include a screenshot attachment control; players can describe the visible board or their game state in text. If an image is supplied through an enabled integration, describe only what is visible and give relevant gameplay guidance.
