"""Local Kannada-script responses for the curated MagicSquare chatbot."""
import re


KANNADA_REFUSAL = "ನಾನು ಮ್ಯಾಜಿಕ್ ಚೌಕ ಮತ್ತು ಈ ವೆಬ್‌ಸೈಟ್‌ಗೆ ಸಂಬಂಧಿಸಿದ ಪ್ರಶ್ನೆಗಳಿಗೆ ಮಾತ್ರ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ."


def kannada_answer(question, english_answer, username=""):
    """Return a Kannada-script answer for a known chatbot topic or a safe fallback."""
    q = re.sub(r"\s+", " ", str(question or "").strip().lower())
    answer = str(english_answer or "").lower()
    both = f"{q} {answer}"

    if english_answer == "I can only help with questions about MagicSquare and gaming related topics.":
        return KANNADA_REFUSAL
    if re.search(r"(?:change|switch|set|reply|answer|speak|talk|chat|language|from now).{0,30}(?:kannada|ಕನ್ನಡ)|ಕನ್ನಡ", q):
        return "ಸರಿ, ಇನ್ನು ಮುಂದೆ ನಾನು ಕನ್ನಡದಲ್ಲೇ ಉತ್ತರಿಸುತ್ತೇನೆ."
    if re.fullmatch(r"(?:hi+|hello|hey+|namaste|ನಮಸ್ಕಾರ|good (?:morning|afternoon|evening))[!. ,]*", q):
        return f"ನಮಸ್ಕಾರ, {username or 'ಗೆಳೆಯರೇ'}! ನಾನು ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?"

    if re.search(r"ramanujan|ರಾಮಾನುಜನ್|date square|birthday square|ಜನ್ಮದಿನ", q):
        return ("ಶ್ರೀನಿವಾಸ ರಾಮಾನುಜನ್ (1887–1920) ಪ್ರಸಿದ್ಧ ಭಾರತೀಯ ಗಣಿತಜ್ಞರು. ಅವರ 4×4 ಜನ್ಮದಿನದ ಮ್ಯಾಜಿಕ್ ಚೌಕದ ಮೊದಲ ಸಾಲಿನಲ್ಲಿ DD, MM, CC ಮತ್ತು YY ಇರುತ್ತವೆ. "
                "ಪ್ರತಿ ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಮುಖ್ಯ ಕರ್ಣಗಳ ಮೊತ್ತ 34. Formula ಪುಟದಲ್ಲಿ ದಿನಾಂಕ ನಮೂದಿಸಿ ಇಂತಹ ಚೌಕವನ್ನು ರಚಿಸಬಹುದು; ದಿನಾಂಕವನ್ನು ಸಂಗ್ರಹಿಸಲಾಗುವುದಿಲ್ಲ.")
    if re.search(r"2\s*[x×]\s*2|2x2|2×2|2 ಬೈ 2|ಎರಡು ಬೈ ಎರಡು", q):
        return "ಸಾಮಾನ್ಯ 2×2 ಮ್ಯಾಜಿಕ್ ಚೌಕ ಅಸ್ತಿತ್ವದಲ್ಲಿಲ್ಲ. ನಾಲ್ಕು ವಿಭಿನ್ನ ಸಂಖ್ಯೆಗಳೊಂದಿಗೆ ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಎರಡೂ ಕರ್ಣಗಳ ಮೊತ್ತವನ್ನು ಒಂದೇ ಸಮನಾಗಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ."
    if re.search(r"magic constant|target sum|formula|ಸ್ಥಿರಾಂಕ|ಗುರಿ ಮೊತ್ತ", q):
        order = re.search(r"(\d{1,2})\s*[x×]\s*\d{1,2}", q)
        if order and 1 <= int(order.group(1)) <= 10:
            n = int(order.group(1))
            return f"ಮ್ಯಾಜಿಕ್ ಸ್ಥಿರಾಂಕವು ಪ್ರತಿ ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಕರ್ಣದ ಗುರಿ ಮೊತ್ತ. ಸೂತ್ರ M(n)=n(n²+1)/2. {n}×{n} ಚೌಕಕ್ಕೆ ಗುರಿ ಮೊತ್ತ {n * (n*n+1)//2}."
        return "ಮ್ಯಾಜಿಕ್ ಸ್ಥಿರಾಂಕವು ಪ್ರತಿ ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಮುಖ್ಯ ಕರ್ಣಗಳ ಗುರಿ ಮೊತ್ತ. n ಕ್ರಮದ ಸಾಮಾನ್ಯ ಚೌಕಕ್ಕೆ ಸೂತ್ರ M(n)=n(n²+1)/2."
    if re.search(r"siamese|odd order|odd size|ವಿಷಮ ಕ್ರಮ", q):
        return "ವಿಷಮ ಕ್ರಮದ ಚೌಕಗಳಿಗೆ Siamese ವಿಧಾನ ಬಳಸಿ: ಮೇಲಿನ ಸಾಲಿನ ಮಧ್ಯದಿಂದ ಆರಂಭಿಸಿ, ಪ್ರತಿ ಮುಂದಿನ ಸಂಖ್ಯೆಯನ್ನು ಒಂದು ಮನೆ ಮೇಲಕ್ಕೆ ಮತ್ತು ಬಲಕ್ಕೆ ಇಡಿ. ಅಂಚು ದಾಟಿದರೆ ಎದುರುಬದಿಗೆ ಸುತ್ತಿ; ಮನೆ ತುಂಬಿದ್ದರೆ ಹಿಂದಿನ ಸಂಖ್ಯೆಯಿಂದ ಒಂದು ಮನೆ ಕೆಳಗೆ ಇಡಿ."
    if re.search(r"doubly even|divisible by 4|complement|4x4.{0,20}8x8", q):
        return "4×4 ಮತ್ತು 8×8 ಮುಂತಾದ ನಾಲ್ಕರಿಂದ ಭಾಗವಾಗುವ ಕ್ರಮಗಳಿಗೆ doubly-even complement ವಿಧಾನ ಬಳಸಿ. 1ರಿಂದ n²ವರೆಗೆ ತುಂಬಿ, ಗುರುತಿಸಿದ ಕರ್ಣದ ಮನೆಗಳಲ್ಲಿ ಸಂಖ್ಯೆಯನ್ನು n²+1ರಿಂದ ಕಡಿತಗೊಳಿಸಿದ ಪೂರಕ ಸಂಖ್ಯೆಯಿಂದ ಬದಲಾಯಿಸಿ."
    if re.search(r"strachey|lux|singly even|6x6|10x10", q):
        return "6×6 ಮತ್ತು 10×10 ಮುಂತಾದ singly-even ಕ್ರಮಗಳಿಗೆ Strachey/LUX ವಿಧಾನ ಬಳಸಿ. ಚೌಕವನ್ನು ನಾಲ್ಕು ಉಪಚೌಕಗಳಾಗಿ ವಿಭಜಿಸಿ, odd-order ಚೌಕಗಳನ್ನು ಆಫ್‌ಸೆಟ್‌ಗಳೊಂದಿಗೆ ತುಂಬಿ, ನಿರ್ದಿಷ್ಟ ಕಾಲಮ್‌ಗಳನ್ನು ವಿನಿಮಯ ಮಾಡಲಾಗುತ್ತದೆ."
    if re.search(r"what is a magic square|define|meaning of magic square|a grid of different numbers|ಮ್ಯಾಜಿಕ್ ಸ್ಕ್ವೇರ್ ಎಂದರೇನು|ಮ್ಯಾಜಿಕ್ ಸ್ಕ್ವೇರ್ ಅಂದರೆ", q):
        return "ಮ್ಯಾಜಿಕ್ ಚೌಕವೆಂದರೆ ಸಂಖ್ಯೆಗಳ ಚೌಕಾಕಾರದ ಜೋಡಣೆ. ಪ್ರತಿಯೊಂದು ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಎರಡೂ ಮುಖ್ಯ ಕರ್ಣಗಳ ಮೊತ್ತ ಒಂದೇ ಆಗಿರುತ್ತದೆ. ಸಾಮಾನ್ಯ n×n ಚೌಕದಲ್ಲಿ 1ರಿಂದ n²ವರೆಗಿನ ಪ್ರತಿಯೊಂದು ಸಂಖ್ಯೆಯನ್ನು ಒಂದೇ ಬಾರಿ ಬಳಸಲಾಗುತ್ತದೆ."
    if re.search(r"4\s*[x×]\s*4|4x4|4×4", q) or "4×4 magic square" in answer:
        return "4×4 ಸಾಮಾನ್ಯ ಮ್ಯಾಜಿಕ್ ಚೌಕದಲ್ಲಿ 1ರಿಂದ 16ರವರೆಗಿನ ಸಂಖ್ಯೆಗಳು ಒಂದೊಂದು ಬಾರಿ ಬರುತ್ತವೆ. ಪ್ರತಿ ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಎರಡೂ ಮುಖ್ಯ ಕರ್ಣಗಳ ಮೊತ್ತ 34. ರಾಮಾನುಜನ್ ಅವರ ಜನ್ಮದಿನದ ಚೌಕವೂ 4×4 ಆಗಿದೆ."
    if re.search(r"rule|same number|repeat|duplicate|ನಿಯಮ|ಒಂದೇ ಸಂಖ್ಯೆ", q):
        return "1ರಿಂದ n²ವರೆಗಿನ ಪ್ರತಿಯೊಂದು ಸಂಖ್ಯೆಯನ್ನು ಒಂದೇ ಬಾರಿ ಬಳಸಿ. ಪ್ರತಿಯೊಂದು ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಎರಡೂ ಮುಖ್ಯ ಕರ್ಣಗಳ ಮೊತ್ತ ಮ್ಯಾಜಿಕ್ ಸ್ಥಿರಾಂಕಕ್ಕೆ ಸಮವಾಗಿರಬೇಕು."
    if re.search(r"board sizes|available sizes|size range|sizes can i play|ಗಾತ್ರ", q):
        return "ಆಟದಲ್ಲಿ 3×3ರಿಂದ 10×10ರವರೆಗಿನ ಗಾತ್ರಗಳಿವೆ. 2×2 ಸಾಮಾನ್ಯ ಮ್ಯಾಜಿಕ್ ಚೌಕ ಸಾಧ್ಯವಿಲ್ಲ."
    if re.search(r"how to play|how do i play|swap puzzle|swap tiles|swap mode|ಆಟ ಹೇಗೆ", q):
        return "Play ಪುಟದಲ್ಲಿ ಗಾತ್ರ ಆಯ್ಕೆಮಾಡಿ. Swap mode‌ನಲ್ಲಿ ಎರಡು ಸಂಖ್ಯೆಗಳನ್ನು ಆಯ್ದು ಪರಸ್ಪರ ಬದಲಾಯಿಸಿ; ಎಲ್ಲ ಸಾಲು, ಕಾಲಮ್ ಮತ್ತು ಕರ್ಣಗಳು ಗುರಿ ಮೊತ್ತ ತಲುಪುವವರೆಗೆ ಮುಂದುವರಿಸಿ."
    if re.search(r"fill mode|fill the square|manual mode|practice mode|manual practice", q):
        return "Fill mode‌ನಲ್ಲಿ ಖಾಲಿ ಚೌಕಕ್ಕೆ 1ರಿಂದ n²ವರೆಗಿನ ಸಂಖ್ಯೆಯನ್ನು ಒಂದೊಂದಾಗಿ ನಮೂದಿಸಿ; ಒಂದು ಸುತ್ತಿಗೆ ಮೂರು ಪರಿಶೀಲನೆಗಳಿವೆ. Manual mode ಅಭ್ಯಾಸಕ್ಕಾಗಿ, ಫಲಿತಾಂಶಕ್ಕೆ ಅಂಕ ನೀಡುವುದಿಲ್ಲ."
    if re.search(r"hint|stuck|strategy|what should i do next|ಸುಳಿವು", q):
        return "ಸುಳಿವು ಒಂದು ಉಪಯುಕ್ತ ವಿನಿಮಯವನ್ನು ತೋರಿಸುತ್ತದೆ; ಅದು ಸ್ವಯಂ ಚಲನೆ ಮಾಡುವುದಿಲ್ಲ. ಪ್ರತಿ ಸುಳಿವಿಗೆ 15 ಸೆಕೆಂಡು ಸೇರುತ್ತದೆ. ಮೊದಲು ಗುರಿಗೆ ಹತ್ತಿರವಿರುವ ಸಾಲು ಮತ್ತು ಕಾಲಮ್‌ಗಳನ್ನು ನೋಡಿ."
    if re.search(r"daily challenge|daily puzzle|streak|ದೈನಂದಿನ ಸವಾಲು", q):
        return "Daily Challenge ಎಲ್ಲರಿಗೂ ಒಂದೇ ದಿನದ ಚೌಕವನ್ನು ನೀಡುತ್ತದೆ ಮತ್ತು ಪ್ರತಿದಿನ 00:00 UTCಗೆ ಮರುಹೊಂದಿಸುತ್ತದೆ. ಗಾತ್ರಗಳನ್ನು ಕ್ರಮವಾಗಿ ಪೂರ್ಣಗೊಳಿಸಿ ನಿಮ್ಮ streak ಮುಂದುವರಿಸಿ."
    if re.search(r"leaderboard|leader board|ranking|ಲೀಡರ್.?ಬೋರ್ಡ್", q):
        return "Leaderboard ವೇಗವಾದ Swap mode ಪರಿಹಾರಗಳನ್ನು ತೋರಿಸುತ್ತದೆ. ಸಮಯ ಕಡಿಮೆ ಇದ್ದವರು ಮೇಲಿರುತ್ತಾರೆ; ಸಮಾನ ಸಮಯದಲ್ಲಿ ಕಡಿಮೆ ಚಲನೆ ಮಾಡಿದವರು ಮೇಲಿರುತ್ತಾರೆ. Fill mode ಫಲಿತಾಂಶಗಳು ಇದರಲ್ಲಿ ಸೇರುವುದಿಲ್ಲ."
    if re.search(r"achievement|badge|streak|ಅಚೀವ್|ಬ್ಯಾಡ್ಜ್", q):
        return "Dashboard‌ನಲ್ಲಿ ಬ್ಯಾಡ್ಜ್‌ಗಳು ಮತ್ತು ಪ್ರಗತಿಯನ್ನು ನೋಡಬಹುದು. ವಿವಿಧ ಗಾತ್ರಗಳನ್ನು ಪೂರ್ಣಗೊಳಿಸಿ, ಸುಳಿವುಗಳಿಲ್ಲದೆ ಪರಿಹರಿಸಿ, ಮತ್ತು Daily Challenge ಅನ್ನು ಸತತ ದಿನಗಳಲ್ಲಿ ಆಡಿ ಹೊಸ ಬ್ಯಾಡ್ಜ್‌ಗಳನ್ನು ಗಳಿಸಿ."
    if re.search(r"dashboard|progress|my stats|best time|ಡ್ಯಾಶ್.?ಬೋರ್ಡ್|ಪ್ರಗತಿ", q):
        return "ಮೇಲಿನ ಮೂರು-ಗೆರೆ ಮೆನು ತೆರೆದು Dashboard ಆಯ್ಕೆಮಾಡಿ. ಅಲ್ಲಿ ನಿಮ್ಮ ಉತ್ತಮ ಸಮಯಗಳು, ಪ್ರಯತ್ನಗಳ ಇತಿಹಾಸ, ಪ್ರಗತಿ, streak ಮತ್ತು ಬ್ಯಾಡ್ಜ್‌ಗಳನ್ನು ಕಾಣಬಹುದು."
    if re.search(r"hamburger|three.line|navigation menu|site menu|main menu|what is in the menu|menu.{0,20}(?:contain|include|item)|three-ಗೆರೆ|ಮೆನು", q):
        return "ಶೀರ್ಷಿಕೆಯ ಬಳಿಯ ಮೂರು-ಗೆರೆ ಮೆನು ತೆರೆಯಿರಿ. ಅದರಲ್ಲಿ Play, Daily Challenge, Manual, Dashboard, Leaderboard, Formula ಮತ್ತು Change Theme ಇವೆ. ಐಕಾನ್ ಮತ್ತೊಮ್ಮೆ ಅಥವಾ ಹೊರಗೆ ಒತ್ತಿದರೆ ಮೆನು ಮುಚ್ಚುತ್ತದೆ."
    if re.search(r"profile|logout|log out|sign out|password|email|export|delete account|ಪ್ರೊಫೈಲ್", q):
        return "ಮೇಲಿನ ಬಲಭಾಗದ Profile ತೆರೆಯಿರಿ. ಅಲ್ಲಿ Change Password, Email, Export Your Data, Delete Account ಮತ್ತು Logout ಆಯ್ಕೆಗಳಿವೆ. Logout ನಿಮ್ಮ ಖಾತೆಯಿಂದ ಹೊರಹಾಕುತ್ತದೆ."
    if re.search(r"theme|color|ಬಣ್ಣ|ಥೀಮ್", q):
        return "ಮೂರು-ಗೆರೆ ಮೆನು ತೆರೆದು Change Theme ಆಯ್ಕೆಮಾಡಿ. ಬಯಸಿದ ಬಣ್ಣದ ಥೀಮ್ ಆಯ್ಕೆ ಮಾಡಿದರೆ ಅದು ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಉಳಿಯುತ್ತದೆ."
    if re.search(r"website|web site|site|app|feature|navigation|navigate|what can i do|this website|this site", q):
        return "ಇದು ರಾಮಾನುಜನ್ ಅವರ ಮ್ಯಾಜಿಕ್ ಚೌಕ ಆಧಾರಿತ ಪಜಲ್ ಆಟ. ಮೂರು-ಗೆರೆ ಮೆನುವಿನಿಂದ ಆಟದ ಪುಟಗಳು, Daily Challenge ಮತ್ತು Formula ತೆರೆಯಬಹುದು. Profile‌ನಲ್ಲಿ ಖಾತೆ ಆಯ್ಕೆಗಳು, Dashboard‌ನಲ್ಲಿ ಪ್ರಗತಿ ಮತ್ತು Leaderboard‌ನಲ್ಲಿ ವೇಗದ ಫಲಿತಾಂಶಗಳಿವೆ."
    if re.search(r"voice|microphone|speak|voice chat|ಧ್ವನಿ", q):
        return "Voice chat ತೆರೆಯಲು chatbot‌ನ Voice ಬಟನ್ ಒತ್ತಿ. ಮೈಕ್ರೊಫೋನ್ ಒತ್ತಿ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ ಪ್ರಶ್ನೆ ಕೇಳಿ; ಆಯ್ದ Kannada ಭಾಷೆಯಲ್ಲಿ ಉತ್ತರವನ್ನು ಕೇಳಬಹುದು."

    return "ನಾನು ಮ್ಯಾಜಿಕ್ ಚೌಕ ಮತ್ತು ಈ ವೆಬ್‌ಸೈಟ್ ಬಗ್ಗೆ ಸಹಾಯ ಮಾಡಬಹುದು. ನಿಯಮಗಳು, ಗುರಿ ಮೊತ್ತ, ಆಟದ ವಿಧಾನಗಳು, ಸುಳಿವುಗಳು, Dashboard ಅಥವಾ Profile ಬಗ್ಗೆ ಕೇಳಿ."


def kannada_suggestions(suggestions):
    labels = {
        "How to play": "ಆಟ ಹೇಗೆ ಆಡಬೇಕು", "Magic constant": "ಮ್ಯಾಜಿಕ್ ಸ್ಥಿರಾಂಕ",
        "Daily Challenge": "ದೈನಂದಿನ ಸವಾಲು", "Dashboard": "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
        "Hints": "ಸುಳಿವುಗಳು", "Rules": "ನಿಯಮಗಳು", "Game modes": "ಆಟದ ವಿಧಾನಗಳು",
        "I'm stuck": "ನನಗೆ ಸಹಾಯ ಬೇಕು", "The game": "ಆಟದ ಬಗ್ಗೆ", "Magic squares": "ಮ್ಯಾಜಿಕ್ ಚೌಕಗಳು",
        "My current board": "ನನ್ನ ಚೌಕ", "Swap puzzle": "Swap ಪಜಲ್", "Fill the square": "ಚೌಕ ತುಂಬಿಸಿ",
        "Manual mode": "Manual ಅಭ್ಯಾಸ", "How hints work": "ಸುಳಿವು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
        "Hint penalty": "ಸುಳಿವಿನ ಸಮಯದ ದಂಡ", "How it works": "ಇದು ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ",
        "Why sizes are locked": "ಗಾತ್ರಗಳು ಏಕೆ ಲಾಕ್ ಆಗಿವೆ", "Streaks": "ಸತತ ದಿನಗಳ ಆಟ",
        "Reset time": "ಮರುಹೊಂದಿಸುವ ಸಮಯ", "Global leaderboard": "ಜಾಗತಿಕ ಲೀಡರ್‌ಬೋರ್ಡ್",
        "Daily board": "ದೈನಂದಿನ ಲೀಡರ್‌ಬೋರ್ಡ್", "How to get on it": "ಲೀಡರ್‌ಬೋರ್ಡ್‌ಗೆ ಸೇರುವುದು ಹೇಗೆ",
        "My best times": "ನನ್ನ ಉತ್ತಮ ಸಮಯಗಳು", "List all": "ಎಲ್ಲ ಬ್ಯಾಡ್ಜ್‌ಗಳು",
        "Speed Demon": "Speed Demon", "Night Owl": "Night Owl", "Streak badges": "streak ಬ್ಯಾಡ್ಜ್‌ಗಳು",
        "Change password": "ಪಾಸ್‌ವರ್ಡ್ ಬದಲಿಸಿ", "Add email": "ಇಮೇಲ್ ಸೇರಿಸಿ",
        "Export data": "ಡೇಟಾ ರಫ್ತು ಮಾಡಿ", "Delete account": "ಖಾತೆ ಅಳಿಸಿ", "Forgot password": "ಪಾಸ್‌ವರ್ಡ್ ಮರೆತಿದ್ದೇನೆ",
        "English": "English", "ಕನ್ನಡ": "ಕನ್ನಡ",
    }
    return [{"label": labels.get(item, item), "question": item} for item in suggestions]

