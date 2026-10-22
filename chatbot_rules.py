"""Deterministic, curated responses for the SquareVerse companion."""
import re


FALLBACK = "I'm not sure I understood that. I can help with these topics."
FALLBACK_CHIPS = ["How to play", "Hints", "Daily Challenge", "Scores", "Account"]
OFF_TOPIC = "I can only help with questions about MagicSquare and gaming related topics."


def _entry(message, chips=None):
    return message, chips or []


def answer_for(question, username="there", context=None):
    """Return (answer, suggestion labels, in_scope) using ordered phrase rules."""
    text = re.sub(r"\s+", " ", question.lower().strip())
    compact = re.sub(r"[^a-z0-9×]+", " ", text).strip()

    # Clarifications come before their more general topic matches.
    vague = [
        (r"^(?:help|i need help|can you help me)[!. ]*$", "I can help with these topics. What would you like to know?", ["How to play", "Hints", "Daily Challenge", "Scores", "Account"]),
        (r"^(?:explain|tell me more|more details)[!. ]*$", "What should I explain? The game, magic squares, or something on screen?", ["The game", "Magic squares", "My current board"]),
        (r"^(?:i'?m confused|i am confused|confused)[!. ]*$", "No problem. Are you stuck on the rules, a specific mode, or your current puzzle?", ["Rules", "Game modes", "I'm stuck"]),
        (r"^(?:it'?s not working|something is wrong|it is not working|not working)[!. ]*$", "What isn't working? Login, saving a result, the board, or the chat? If you see an error message, tell me what it says.", []),
        (r"^(?:method|methods|algorithm|construction)(?:\s*/\s*(?:method|methods|algorithm|construction))?[!. ]*$", "Which size type do you mean?", ["Odd sizes", "Divisible by 4", "6 and 10"]),
        (r"^(?:ramanujan|formula)(?:\s*/\s*(?:ramanujan|formula))?[!. ]*$", "Do you want to know who Ramanujan was or how to build the date square?", ["Who was he", "Build my square", "Magic constant"]),
        (r"^(?:how do i play|how to play|game modes|modes)[!. ]*$", "Which mode do you want to learn?", ["Swap puzzle", "Fill the square", "Daily Challenge", "Manual mode"]),
        (r"^(?:hint|hints)[!. ]*$", "Do you want to know how hints work or need help with your current board?", ["How hints work", "Hint penalty", "I'm stuck"]),
        (r"^(?:daily|daily challenge)(?:\s*/\s*(?:daily|daily challenge))?[!. ]*$", "What would you like to know about it?", ["How it works", "Why sizes are locked", "Streaks", "Reset time"]),
        (r"^(?:score|scores|time)(?:\s*/\s*(?:score|scores|time))?[!. ]*$", "Do you mean how time is measured, the leaderboard, or your best times?", ["How time is measured", "Leaderboard", "My best times"]),
        (r"^(?:leaderboard|leader board)[!. ]*$", "Do you mean the global board or the daily board?", ["Global leaderboard", "Daily board", "How to get on it"]),
        (r"^(?:badges|achievements)[!. ]*$", "Do you want the full list or how to earn a specific one?", ["List all", "Speed Demon", "Night Owl", "Streak badges"]),
        (r"^(?:account|profile)[!. ]*$", "What do you need?", ["Change password", "Add email", "Export data", "Delete account"]),
        (r"^password[!. ]*$", "Did you forget it or do you want to change it?", ["Forgot password", "Change password"]),
        (r"^(?:language|chat language)[!. ]*$", "Do you want to change the chat language?", ["English", "ಕನ್ನಡ"]),
        (r"^(?:daily challenge|daily)[!. ]+(?:help|info|details)$", "What would you like to know about it?", ["How it works", "Why sizes are locked", "Streaks", "Reset time"]),
        (r"^(?:score|time)[!. ]+(?:help|info|details)$", "Do you mean how time is measured, the leaderboard, or your best times?", ["How time is measured", "Leaderboard", "My best times"]),
        (r"^(?:is there multiplayer|multiplayer)[?!. ]*$", "Not currently. The game is single-player with shared daily puzzles and leaderboards. I can still give strategy tips.", []),
    ]
    for pattern, message, chips in vague:
        if re.fullmatch(pattern, text, re.I):
            return _entry(message, chips) + (True,)

    if re.fullmatch(r"(?:hi+|hello|hey+|namaste|ನಮಸ್ಕಾರ|good (?:morning|afternoon|evening))(?: there)?[!. ,]*", text, re.I):
        return _entry(f"Hi, {username or 'player'}, how can I help you?", ["How to play", "Daily Challenge", "Hints"]) + (True,)

    # Common Kannada voice questions map into the same curated English answers.
    kannada_phrases = [
        ("ಮ್ಯಾಜಿಕ್ ಸ್ಕ್ವೇರ್ ಎಂದರೇನು", "what is a magic square"),
        ("ಮ್ಯಾಜಿಕ್ ಸ್ಕ್ವೇರ್ ಅಂದರೆ ಏನು", "what is a magic square"),
        ("ಆಟ ಹೇಗೆ ಆಡಬೇಕು", "how do i play swap puzzle"),
        ("ದೈನಂದಿನ ಸವಾಲು", "how does the daily challenge work"),
        ("ಮ್ಯಾಜಿಕ್ ಸ್ಥಿರಾಂಕ", "what is the magic constant"),
        ("2×2 ಸಾಧ್ಯವಿಲ್ಲ", "why is 2x2 impossible"),
        ("2x2 ಸಾಧ್ಯವಿಲ್ಲ", "why is 2x2 impossible"),
        ("ಸುಳಿವು", "how do hints work"),
        ("ನಿಯಮಗಳು", "what are the game rules"),
        ("ನನ್ನ ಪ್ರಗತಿ", "my progress"),
        ("ಲೀಡರ್‌ಬೋರ್ಡ್", "how does the global leaderboard work"),
    ]
    for phrase, english_query in kannada_phrases:
        if phrase in text:
            text = english_query
            break

    # Chips and short labels route to the same specific answers as typed questions.
    aliases = {
        "the game": "what is squareverse", "magic squares": "what is a magic square", "my current board": "help with my current game board",
        "rules": "what are the game rules", "game modes": "what game modes are available", "i'm stuck": "i am stuck on my magic square puzzle",
        "odd sizes": "explain the siamese method for odd magic square sizes", "divisible by 4": "explain the construction method for 4x4 and 8x8 squares", "6 and 10": "explain the strachey method for 6x6 and 10x10 squares",
        "who was he": "who was ramanujan", "build my square": "how do i build a birthday square", "magic constant": "what is the magic constant",
        "swap puzzle": "how do i play swap puzzle", "fill the square": "how does fill the square work", "manual mode": "what is manual mode",
        "how hints work": "how do hints work", "hint penalty": "does a hint cost anything", "how it works": "how does the daily challenge work", "why sizes are locked": "why are daily challenge sizes locked", "streaks": "how does the streak work", "reset time": "when does it reset",
        "how time is measured": "how is my time measured", "global leaderboard": "how does the global leaderboard work", "daily board": "is there a daily leaderboard", "how to get on it": "how do i get on the leaderboard", "my best times": "where can i see my best times",
        "list all": "list all achievements", "speed demon": "how do i earn speed demon", "night owl": "how do i earn night owl", "streak badges": "streak badges",
        "change password": "how do i change my password", "add email": "how do i add or verify my email", "export data": "how do i download my data", "delete account": "how do i delete my account", "forgot password": "i forgot my password",
        "english": "change chat language to english", "ಕನ್ನಡ": "change chat language to kannada",
    }
    text = aliases.get(text.strip(" ?.!"), text)
    compact = re.sub(r"[^a-z0-9×]+", " ", text.lower()).strip()

    # Curated answers, ordered from specific to general to avoid broad matches.
    size_target = re.search(r"(?:magic constant|target).{0,24}(\d{1,2})\s*[x×]\s*\d{1,2}|(\d{1,2})\s*[x×]\s*\d{1,2}.{0,24}(?:magic constant|target)", text, re.I)
    if size_target:
        n = int(size_target.group(1) or size_target.group(2))
        if 3 <= n <= 10:
            return _entry(f"For a {n}×{n} square, the target is {n}({n}² + 1) / 2 = {n * (n * n + 1) // 2}.") + (True,)
    rules = [
        (r"(?:hamburger|three[- ]line|three lines|navigation menu|site menu|main menu|open the menu|close the menu)", "Use the three-line menu beside the Ramanujan's Magic Square title to open site navigation. It contains Play, Daily Challenge, Manual, Dashboard, Leaderboard, Formula and Change Theme. Click the icon again or click outside the menu to close it."),
        (r"where.{0,20}(?:play|daily challenge|manual|dashboard|leaderboard|formula|change theme)|(?:play|daily challenge|manual|dashboard|leaderboard|formula).{0,25}(?:menu|find|located)|where.{0,20}theme", "Open the three-line menu beside the Ramanujan's Magic Square title. It contains Play, Daily Challenge, Manual, Dashboard, Leaderboard, Formula and Change Theme."),
        (r"where.{0,20}(?:logout|profile)|(?:how|where).{0,20}(?:find|open|access).{0,15}profile|log ?out|sign ?out|profile page|what is profile|profile area", "Select Profile at the top right to manage your email and password, export or delete account data, and find Logout. Clicking Logout ends your sign-in session."),
        (r"(?:what|which).{0,20}(?:is in|does|items? in|links? in).{0,15}(?:menu|navigation)|menu.{0,25}(?:contain|include|have|item)|how.{0,20}(?:navigate|open the menu)", "The three-line menu is beside the Ramanujan's Magic Square title. It contains Play, Daily Challenge, Manual, Dashboard, Leaderboard, Formula and Change Theme. Click the icon again or outside the menu to close it."),
        (r"(?:how|what).{0,35}ramanujan.{0,30}(?:construct|build|made|work|works|function|propert)|(?:construct|build|make).{0,30}ramanujan", "Ramanujan's 4×4 date square starts with DD, MM, CC and YY from his birth date. The remaining entries are arranged so each row, column and main diagonal totals 34. The Formula page builds a date square from a date you enter; the date stays in your browser."),
        (r"how.{0,30}(?:magic squares? work|does a magic square work)|why.{0,25}magic square.{0,15}(?:work|special)", "A normal magic square uses each number from 1 to n² once. The entries are arranged so every row, column and both main diagonals equal the magic constant n(n² + 1) / 2. For a 4×4 square the target is 34."),
        (r"ramanujan.{0,45}(?:how|work|construct|build|properties)|(?:how|why).{0,25}(?:ramanujan'?s|date) square|ramanujan'?s square.{0,30}(?:work|built|construct|property)", "Ramanujan's famous 4×4 date square places DD, MM, CC and YY (the parts of his birth date) across its first row. The other cells are arranged so every row, column and main diagonal sums to 34, the 4×4 magic constant. The Formula page can build a date square from a date you enter; that date is not stored."),
        (r"(?:what is|explain|describe|tell me about).{0,25}(?:4\s*[x×]\s*4|4x4).{0,20}magic square|4\s*[x×]\s*4 magic square|magic square.{0,15}4\s*[x×]\s*4", "A normal 4×4 magic square uses each number from 1 to 16 once, with every row, column and both main diagonals summing to 34. Ramanujan's famous 4×4 version puts DD, MM, CC and YY from his birth date in its first row."),
        (r"what can i do(?: here| on this site)?|how do i use (?:this )?(?:site|website|app)|how does (?:this )?(?:website|site|app) work|website features|features of (?:this )?(?:website|site)", "This site is a magic-square puzzle game. Use the three-line menu for Play, Daily Challenge, Manual, Dashboard, Leaderboard, Formula and Change Theme. Open Profile at the top right to change your password or email, export your data, delete your account or log out."),
        (r"what is this (?:website|site)|what does this (?:website|site) do|what is magic.?square website|what is squareverse game|about (?:this|the) (?:website|site|project)|website about|site about", "This is Ramanujan's Magic Square, an online puzzle game. Play Swap or Fill puzzles, try the Daily Challenge, learn construction methods on Formula, and track your times, streaks and badges on Dashboard. Use the three-line menu for game pages and Profile for account settings."),
        (r"tech stack|what (?:is|are) (?:this )?(?:website|site|project) built with|what technology|backend|frontend technology", "The site uses Python with Flask on the backend, a browser frontend built with HTML, CSS and JavaScript, and SQLite for account and game data."),
        (r"what pages|which pages|where can i find|site navigation|website features|what features|features of (?:this|the) (?:site|website|game)", "Open the three-line menu beside the Ramanujan's Magic Square title for Play, Daily Challenge, Manual, Dashboard, Leaderboard, Formula and Change Theme. Profile is at the top right for account settings, data export and Logout."),
        (r"play page|where do i play|start (?:a )?game|start playing", "Open Play to choose a board size and start a Swap puzzle. Use Daily Challenge for today's shared puzzle, or Manual for unscored practice."),
        (r"dashboard page|what is on (?:the )?dashboard|dashboard show|where.*badges", "Dashboard shows your best times by size, attempt history, progress, daily streak and earned badges. Sign in to save and view your account progress."),
        (r"profile page|profile settings|manage my account|account settings", "Profile lets you manage your email and password, export account data as CSV, and delete your account. Never share your password in chat."),
        (r"what (?:does )?(?:the )?(?:site|website) store|what data.{0,20}store|data does the site store|store about me", "For signed-in accounts the site stores your username and password hash, optional email, puzzle attempts, achievements, daily streak and saved chatbot conversation. Passwords are stored as hashes, not plain text. Your date of birth for the Formula square is not stored."),
        (r"change.*theme|website theme|color theme|theme choice|theme settings|how do themes work|what themes", "Open the three-line menu and choose Change Theme, then select a palette. Your choice is saved in this browser and applied across the site's pages."),
        (r"how.*play.{0,20}(?:\d+\s*[x×]\s*\d+|size)|play.{0,12}(?:\d+\s*[x×]\s*\d+)", "Open Play, choose an unlocked size such as 3×3, then start the Swap puzzle. The goal is to restore the square so every row, column and main diagonal reaches the target sum."),
        (r"admin page|admin dashboard|administrator|manage users|review.*chatbot", "The Admin page is available only to authorized admin accounts. It provides site administration tools, including review of chatbot feedback and reports."),
        (r"does.*multiplayer|multiplayer|play with friends|team play|matchmaking", "MagicSquare is currently a single-player puzzle game. Players can compare results on the leaderboard; live matchmaking and team coordination are not available."),
        (r"where.*(attempt|solve) history|attempt history|past games|previous games", "Open Dashboard and scroll to Attempt history to review saved puzzle results. You need to be signed in for results to be associated with your account."),
        (r"how.*(save|saved)|save my progress|progress saved|without account|guest", "Sign in before playing to save attempts, achievements and streak progress to your account. Guest play may not persist account progress."),
        (r"what is manual|manual practice|practice mode", "Manual is an unscored practice page where you can enter a grid and check its rows, columns and diagonals without recording a competitive result."),
        (r"what is fill|fill mode|fill the square", "Fill mode starts with an empty grid. Enter each value from 1 to n² once, then check your square. You have three checks for the round."),
        (r"what is swap|swap mode|swap puzzle mode", "Swap mode gives you a scrambled valid square. Select two tiles to swap them until the rows, columns and diagonals match the target."),
        (r"what is daily challenge|daily challenge is|daily puzzle", "Daily Challenge is a shared Swap puzzle that changes at midnight UTC. Solve available sizes in order to build your daily streak."),
        (r"magic square.*website|website.*magic square|magic square game", "MagicSquare is the site's puzzle: place each number from 1 through n² once so every row, column and both main diagonals have the same sum. You can play sizes 3×3 through 10×10."),
        (r"(?:what is|define|explain|meaning of).{0,18}magic square|magic square.{0,12}(?:mean|definition)", "A grid of different numbers arranged so that every row, column and both main diagonals add up to the same total. In this game you use the numbers 1 to n² exactly once."),
        (r"what is squareverse|what is ramanujan'?s magic square|ramanujan'?s magic square|magic square of ramanujan", "Ramanujan's Magic Square is a famous 4×4 normal magic square based on his birth date. Its first row is DD, MM, CC and YY; each row, column and main diagonal totals 34. This site lets you explore the square and play related magic-square puzzles."),
        (r"who was ramanujan.{0,25}(?:greatest|bio|born|formal|series)|full bio", "Srinivasa Ramanujan (1887–1920) was an Indian mathematician born in Erode, Tamil Nadu. Despite little formal training in advanced mathematics, he made influential discoveries in number theory, infinite series and continued fractions. His birth-date 4×4 magic square places DD, MM, CC and YY across the first row; every row, column and main diagonal sums to 34."),
        (r"who was ramanujan|ramanujan.{0,20}(?:who|square)|who.{0,15}ramanujan", "Srinivasa Ramanujan (1887–1920) was an Indian mathematician known for original work in number theory and infinite series. His famous 4×4 date square starts with DD, MM, CC and YY and has a magic total of 34 across rows, columns and main diagonals."),
        (r"birthday square|date square|build.{0,20}(?:birthday|date of birth)|date of birth square", "Open the Formula page, pick your date of birth and press 'Build my magic square'. Every row, column and diagonal will add up to the same total."),
        (r"dd.{0,12}mm.{0,12}cc.{0,12}yy|what do.{0,20}(?:dd|mm|cc|yy) mean", "DD is the day, MM is the month, CC is the century, and YY is the two-digit year. These four values form the top row of the date square."),
        (r"date of birth.{0,20}stored|stored.{0,20}birth|store my date", "No. Your date of birth is used in your browser to compute the square and is not stored."),
        (r"numbers shifted|why.{0,20}shift|zero or negative", "Some date-square offsets can create zero or negative cells. The whole square is shifted upward by the same amount so every value is positive and the magic sums stay equal."),
        (r"two cells.{0,20}same|duplicate.{0,20}date square|cells coincide", "Some dates produce two equal cells in this general date-square pattern. The row, column and diagonal sums remain magic, but all 16 values are not guaranteed to be distinct for every date."),
        (r"why.{0,30}(?:formula|n\s*\()|how.{0,15}formula.{0,15}work", "The numbers 1 through n² have an average of (n² + 1) / 2. There are n numbers in each row, so the target is n(n² + 1) / 2."),
        (r"magic constant|row.{0,15}add up|target sum|formula|what does.{0,8}(?:σ|sigma)", "It is the target sum for every row, column and diagonal. The formula is M(n) = n(n² + 1) / 2. The Σ symbol on the board shows this target."),
        (r"targets?.{0,20}(?:size|each|all|4x4)|target for \d+x\d+|all sizes|each size|every size", "3×3 = 15, 4×4 = 34, 5×5 = 65, 6×6 = 111, 7×7 = 175, 8×8 = 260, 9×9 = 369, 10×10 = 505."),
        (r"sizes can i play|board sizes|available sizes|size range", "Every size from 3×3 to 10×10."),
        (r"same number twice|repeat a number|duplicate numbers|numbers.{0,18}once each", "No. Use each number from 1 through n² exactly once."),
        (r"more than one solution|multiple solutions|another solution", "Yes. Most magic-square orders have more than one valid arrangement; this game selects a valid target square for each round."),
        (r"what are the rules|game rules|rules of the game", "Use every number from 1 through n² exactly once. Every row, column and both main diagonals must add up to the same magic constant."),
        (r"(?:formula|magic constant).{0,35}2\s*[x×]\s*2|2\s*[x×]\s*2.{0,45}(?:formula|constant|target)", "The formula gives a target of 5 for n=2, but the row, column and diagonal conditions cannot be met with four distinct numbers. So no 2×2 magic square exists."),
        (r"(?:how are|how do you|how to).{0,35}(?:construct|build).{0,25}magic squares?", "Odd orders use the Siamese method, orders divisible by 4 use a complement pattern, and singly-even orders such as 6×6 and 10×10 use Strachey construction."),
        (r"download.{0,30}(?:image|picture)|save.{0,20}square.{0,20}image", "Use the Download image control on the Play page to save your solved square as an image."),
        (r"hint.{0,25}achievement|achievement.{0,25}hint", "Hints add 15 seconds and are recorded on your attempt. Some achievements, such as No Hints Needed and Clean Run, specifically require solving without hints."),
        (r"2\s*[x×]\s*2|2x2|2×2|why.{0,20}impossible", "The row, column and diagonal conditions force opposite cells to be equal, but all four numbers must be different. So no 2×2 magic square exists."),
        (r"siamese|odd size|odd order", "They use the Siamese method. Start in the middle of the top row and place numbers moving up and right, wrapping around the edges. If the next cell is taken, move down one cell instead."),
        (r"divisible by 4|4x4.{0,20}8x8|complement pattern|doubly even", "They use a complement pattern. Fill the grid 1 to n² in order, then replace numbers on certain diagonal cells with their complement (n² + 1 minus the number)."),
        (r"strachey|lux|6x6.{0,20}10x10|singly even", "They use the Strachey method. Split the square into four odd-sized quadrants, fill each with a Siamese square plus an offset, then swap some columns between the top and bottom halves."),
        (r"why.{0,20}(?:different|three types)|animate|animation|building", "Odd, doubly-even and singly-even orders need different construction patterns to satisfy all row, column and diagonal sums. The board animates each placement to show how the construction method builds the square."),
        (r"how to play swap|swap tiles|goal|how do i win|swap puzzle", "The finished square is shown, then scrambled. Tap two tiles to swap them. Keep swapping until every row, column and diagonal reaches the target."),
        (r"fill the square|type numbers|fill mode", "You start with an empty grid and type every number yourself, using 1 to n² once each. Press 'Check my answer' to see how you did."),
        (r"three tries|3 tries|3 wrong|three checks|attempts.*fill", "You get 3 checks per round. After the third wrong check, the round ends and one valid solution is shown."),
        (r"incomplete|empty grid|empty or incomplete", "No. If any cell is empty, the check is rejected and no attempt is used."),
        (r"resume|unfinished fill|fill round", "An unfinished Fill round can be resumed for up to 30 minutes. Open Fill mode for the same size to continue."),
        (r"manual mode|manual.*scored|scored.*manual", "A free practice mode where you type numbers into an empty grid. Nothing is scored or saved."),
        (r"difference between fill|fill mode.{0,20}manual", "Fill mode is graded: you have 3 checks and your result is saved. Manual mode is practice only, with live feedback and no saving."),
        (r"change the size|size box|type a size|next button|unlock.{0,10}size|unlock 4x4", "On the Play page, type a size like 5x5 in the Size box and press Generate. You can also use the Next button after solving a square. The next size unlocks after the current square is solved and saved."),
        (r"5x5.{0,25}(?:before|until)|before.{0,20}3x3.{0,15}4x4|daily.{0,20}5x5", "Sizes unlock in order. Complete the 3×3 and 4×4 Daily Challenge squares before playing 5×5."),
        (r"green labels|arrows|sums beside|labels beside|green.*column|blue.*row", "They show the target for each row, column and diagonal. A label turns green when that line is correct."),
        (r"undo|reverse.*swap", "Yes, in Swap mode. Press 'Undo move' to reverse your last swap."),
        (r"hint button|how do hints work|star button|hint.*arrow", "The Hint button points to one useful swap with an arrow. It does not make the move for you."),
        (r"hint cost|hint penalty|time increase after a hint|timer increase after a hint", "Yes. Each hint adds 15 seconds to your time and counts as a hint used."),
        (r"hints.*fill|fill.*hints", "No. Hints only exist in Swap mode."),
        (r"stuck|tips|where do i start|too hard|what should i do next|help with my current board", "Start with the target sum. Check which rows and columns are already correct, and prefer swaps that fix more than one line at once. If you are still stuck, use a hint."),
        (r"5x5 faster|solve.{0,10}faster|strategy for", "Use the sum labels to find lines that are close to the target. Fix the largest errors first, and avoid swapping tiles in lines that are already green."),
        (r"daily challenge work|same for everyone|everyone gets", "Everyone gets the same scrambled puzzle each day. You solve sizes in order, from 3×3 up to 10×10."),
        (r"daily.{0,20}(?:locked|can't click|cannot click)|why.*locked|order picker", "Daily sizes must be completed in order. You need to finish the current size before the next one opens, and you can't go back."),
        (r"when does it reset|reset time|midnight utc", "At midnight UTC every day."),
        (r"redo|replay|already solved today", "No. Each size can be completed once per day. Come back after midnight UTC for new puzzles."),
        (r"fill mode.{0,20}daily|daily.{0,20}fill", "No. The Daily Challenge is Swap mode only."),
        (r"streak work|what is a streak|daily streak", "Complete at least one Daily Challenge square each day to extend your streak."),
        (r"streak reset|missed day|miss a day", "Missing a day reduces your streak. Complete a Daily Challenge each day to keep it going."),
        (r"time measured|people cheat|server tracks", "The server tracks your time, not your browser. It also checks your solution, so scores can't be faked from the browser."),
        (r"tie|same time|ranked.{0,10}moves", "Leaderboard ties are ranked by solve time first, then by the number of moves."),
        (r"2x2.{0,20}leaderboard|2×2.{0,20}leaderboard|leaderboard.{0,20}2x2", "There is no 2×2 leaderboard because a normal 2×2 magic square is mathematically impossible."),
        (r"is there a daily leaderboard|daily board", "Yes. The site has a Daily Challenge leaderboard for each board size, showing the fastest times for today's challenge."),
        (r"get on the leaderboard|leaderboard work|global leaderboard|daily leaderboard|daily board", "Solve a square in Swap mode. The leaderboard ranks the fastest times for each size."),
        (r"not on the leaderboard|fill score|fill-mode solves|why.*leaderboard", "Only Swap mode solves count for the global leaderboard. Fill mode results are saved to your history but not ranked."),
        (r"where can i see.*(?:progress|best time)|my progress|my best times?|stats and records|my stats|how am i doing|show my progress", "Open the Dashboard. It shows your best time for each size, your attempt history and your badges."),
        (r"what should i try next|what to try next|what next", "Try the next unlocked board size, or take on today's Daily Challenge to build your streak."),
        (r"register|create an account|sign up|log in|login", "Use the Register tab on the home page to create an account with a username and password. On another device, open the same website and log in with those credentials to access the same saved account data."),
        (r"what data.{0,20}store|data does the site store|store about me", "The site stores your username and password hash, optional email, puzzle attempts, achievements, daily streak and saved chatbot conversation. Passwords are stored as hashes, not plain text."),
        (r"result didn't save|result did not save|attempt didn't save|attempt.{0,20}save|save.{0,20}attempt", "Check that you are logged in and connected. If the message says it couldn't save, try again. You can also check your Dashboard history to confirm."),
        (r"list all achievements|list all badges", "First Square, Full Spectrum, Ten and Counting, Speed Demon, No Hints Needed, Daily Devotee, Combo Starter, Puzzle Veteran, Triple Streak, Weeklong Wizard, Clean Run, Mode Hopper and Night Owl."),
        (r"speed demon", "Solve 3×3 in under 20 seconds, 5×5 under 1 minute, 7×7 under 10 minutes, or 9×9 under 5 minutes."),
        (r"full spectrum", "Solve at least one square of every size from 3×3 to 10×10."),
        (r"no hints needed", "Solve a 7×7 or larger square without using any hints."),
        (r"clean run", "Complete 5 puzzles without using a hint."),
        (r"mode hopper", "Complete a Swap puzzle, a Fill puzzle and at least one Daily Challenge."),
        (r"night owl", "Complete a puzzle between 10 PM and 4 AM UTC."),
        (r"triple streak|weeklong wizard|streak badges", "Complete Daily Challenges on 3 consecutive days for Triple Streak, or 7 consecutive days for Weeklong Wizard."),
        (r"first square|ten and counting|combo starter|puzzle veteran", "Complete 1, 10, 5 and 25 puzzle attempts respectively."),
        (r"forgot.*password|can't log in|cannot log in", "Use 'Forgot your password?' on the login page and enter your email. This only works if you saved an email on your account."),
        (r"reset email|didn't get.*email", "Check your spam folder. Reset links expire after 30 minutes. If you never added an email to your account, a reset isn't possible."),
        (r"change.*password", "Go to your Profile page, open 'Change password', enter your current password and the new one (at least 8 characters)."),
        (r"add or verify.*email|verify.*email", "On the Profile page, enter your email and save. Then open the verification link sent to you. Links last 24 hours, and you can request a new one."),
        (r"download.*data|export.*data", "On the Profile page, press 'Download account data (CSV)'."),
        (r"delete.*account", "On the Profile page, press 'Delete my account' and confirm with your password. This permanently removes your attempts and achievements."),
        (r"chat language|reply in kannada|change.*kannada|kannada", "This chat's answers are provided in English. You can choose ಕನ್ನಡ in the language selector to recognize Kannada voice input."),
        (r"voice chat|use voice|voice button|microphone", "Open the MagicSquare companion, tap Voice, then tap the microphone and speak. The browser transcribes your question and reads the reply aloud using a voice available on your device."),
        (r"does.{0,15}(?:chatbot|companion).{0,15}ai|is.{0,15}(?:chatbot|companion).{0,15}ai|rule based|rule-based", "The MagicSquare companion is rule-based. It matches questions to curated answers and does not send your messages to an AI service."),
        (r"screenshot|send a screenshot|image analysis", "Screenshot analysis is not available in this rule-based chat."),
        (r"remember.*history|chat history|clear history", "For logged-in users, chat history is saved. Use the 'Clear history' button to remove it."),
        (r"timer.*wrong|time.*wrong", "Each hint adds 15 seconds to your displayed time. The saved time is measured by the server from when you started."),
        (r"page isn't loading|page is not loading|game.*crash|game isn't loading|game is not loading", "Try refreshing the page and logging in again. If it keeps happening, contact the site administrator."),
        (r"current board|which rows|rows.*correct|explain.*board", "Check the live sum labels beside your board. Green labels mark rows, columns, or diagonals that already match the target."),
        (r"install|run locally|session_secret|openai_api_key|ai chat|ai mode", "Install the packages in requirements.txt, set SESSION_SECRET to a long random value, run python app.py, and open http://localhost:3000. Chat replies are rule-based and do not need an AI key."),
    ]
    for pattern, message in rules:
        if re.search(pattern, text, re.I):
            if pattern.startswith("screenshot") and "screenshot" in text:
                return _entry(message) + (True,)
            return _entry(message) + (True,)

    # Short direct topic requests also resolve to useful curated answers.
    if re.fullmatch(r"how to play|help with account|account help", compact):
        return _entry("The finished square is shown, then scrambled. Tap two tiles to swap them. Keep swapping until every row, column and diagonal reaches the target.") + (True,)
    # Broadly recognize site and puzzle terms so a related question gets a
    # useful orientation response instead of an unrelated-topic refusal.
    scope_words = r"magic square|squareverse|ramanujan|game|gaming|puzzle|daily|challenge|leaderboard|badge|achievement|hint|fill mode|swap|manual|board|grid|account|login|password|email|profile|dashboard|progress|streak|timer|time|formula|constant|square|website|web site|site|page|feature|chat language|kannada|screenshot|install|run locally|theme|score|stats|statistic|record|attempt|solve|next|admin|browser|data|support|help|menu|navigation|navigate|\b\d+\s*[x×]\s*\d+|size|ಮ್ಯಾಜಿಕ್|ಆಟ|ಒಗಟು|ಸವಾಲು|ಸುಳಿವು|ನಿಯಮ|ಪ್ರಗತಿ|ಲೀಡರ್‌ಬೋರ್ಡ್"
    in_scope = bool(re.search(scope_words, text, re.I))
    if in_scope:
        if re.search(r"magic square|squareverse|ramanujan|website|web site|\bsite\b|\bgame\b|\bpuzzle\b|\bmenu\b|navigation|navigate", text, re.I):
            return _entry("MagicSquare is a puzzle game based on normal magic squares. Use each number from 1 to n² once so every row, column and main diagonal has the same sum. This site offers Swap, Fill and Manual play, a Daily Challenge, construction guides, a progress dashboard, badges, leaderboards and account tools. Which part would you like help with?", ["How to play", "Magic constant", "Daily Challenge", "Dashboard"] ) + (True,)
        return _entry(FALLBACK, FALLBACK_CHIPS) + (True,)
    return _entry(OFF_TOPIC) + (False,)

