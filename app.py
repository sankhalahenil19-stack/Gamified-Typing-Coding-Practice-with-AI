from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from collections import Counter
import os
import requests
import json

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-before-deploy-please")

# ================= GEMINI API =================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

def call_gemini(prompt: str, max_tokens: int = 1024) -> str:
    if not GEMINI_API_KEY:
        return None
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7, "topP": 0.9}
    }
    try:
        resp = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            headers=headers, json=payload, timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except Exception as e:
        print(f"[Gemini Error] {e}")
        return None

# ================= DATABASE =================
def get_db():
    return sqlite3.connect("database.db")

def create_tables():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS results(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, wpm REAL, accuracy REAL, missed_keys TEXT, timings TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT, input_format TEXT, output_format TEXT, sample_input TEXT, sample_output TEXT, starter_code TEXT, difficulty TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS submissions(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, question_id INTEGER, code TEXT, status TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS user_xp(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER UNIQUE, xp INTEGER DEFAULT 0, streak INTEGER DEFAULT 0, last_race_date TEXT DEFAULT '')""")
    cur.execute("""CREATE TABLE IF NOT EXISTS achievements(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, badge TEXT, earned_at DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit()
    conn.close()

def insert_sample_questions():
    conn = get_db()
    cur = conn.cursor()
    # starter_code is a blank TEMPLATE — the user must write the solution themselves
    questions = [
        # ── EASY ─────────────────────────────────────────────────────────────
        ('Hello World',
         'Print exactly: Hello, World!',
         'none', 'Hello, World!', '', 'Hello, World!',
         '# Print Hello, World!\nprint(___)',
         'Easy'),
        ('Sum of Two Numbers',
         'Read two integers on one line and print their sum.',
         'a b', 'sum', '3 7', '10',
         'a, b = map(int, input().split())\n# Write your solution below\n',
         'Easy'),
        ('Square a Number',
         'Read an integer n and print n squared.',
         'n', 'n*n', '6', '36',
         'n = int(input())\n# Write your solution below\n',
         'Easy'),
        ('Even or Odd',
         'Read an integer. Print "Even" if it is even, else print "Odd".',
         'n', 'Even or Odd', '7', 'Odd',
         'n = int(input())\n# Write your solution below\n',
         'Easy'),
        ('Absolute Value',
         'Read an integer n (possibly negative) and print its absolute value.',
         'n', '|n|', '-15', '15',
         'n = int(input())\n# Hint: use abs()\n',
         'Easy'),
        # ── MEDIUM ───────────────────────────────────────────────────────────
        ('Max of Three',
         'Read three integers and print the largest one.',
         'a b c', 'max', '4 9 2', '9',
         'a, b, c = map(int, input().split())\n# Write your solution below\n',
         'Medium'),
        ('Sum 1 to N',
         'Read n and print the sum 1+2+3+...+n.',
         'n', 'sum', '5', '15',
         'n = int(input())\n# Use a loop or a formula\n',
         'Medium'),
        ('Count Vowels',
         'Read a lowercase word and print how many vowels (a,e,i,o,u) it contains.',
         'word', 'count', 'hello', '2',
         'word = input()\n# Count occurrences of vowels\n',
         'Medium'),
        ('Reverse a String',
         'Read a string and print it reversed.',
         'string', 'reversed', 'python', 'nohtyp',
         's = input()\n# Write your solution below\n',
         'Medium'),
        ('FizzBuzz (single)',
         'Read n. Print "FizzBuzz" if divisible by both 3 and 5, "Fizz" if by 3, "Buzz" if by 5, else print n.',
         'n', 'result', '15', 'FizzBuzz',
         'n = int(input())\n# Check divisibility\n',
         'Medium'),
        # ── HARD ─────────────────────────────────────────────────────────────
        ('Factorial',
         'Read n (0 <= n <= 12) and print n! (n factorial).',
         'n', 'n!', '5', '120',
         'n = int(input())\nresult = 1\n# Compute factorial and print result\n',
         'Hard'),
        ('Is Prime',
         'Read n. Print "Prime" if n is a prime number, else print "Not Prime".',
         'n', 'Prime/Not Prime', '13', 'Prime',
         'n = int(input())\n# Check if n is prime\n',
         'Hard'),
        ('Fibonacci Nth Term',
         'Read n (0-indexed) and print the nth Fibonacci number. F(0)=0, F(1)=1.',
         'n', 'F(n)', '7', '13',
         'n = int(input())\n# Calculate nth Fibonacci number\n',
         'Hard'),
        ('Palindrome Check',
         'Read a string. Print "Yes" if it is a palindrome, else "No".',
         'string', 'Yes/No', 'racecar', 'Yes',
         's = input()\n# Check if s reads the same forwards and backwards\n',
         'Hard'),
        ('Binary to Decimal',
         'Read a binary number as a string and print its decimal (base-10) value.',
         'binary_string', 'decimal', '1010', '10',
         'b = input()\n# Convert binary string to decimal integer\n',
         'Hard'),
    ]
    cur.executemany(
        """INSERT INTO questions
           (title,description,input_format,output_format,sample_input,sample_output,starter_code,difficulty)
           VALUES (?,?,?,?,?,?,?,?)""",
        questions
    )
    conn.commit()
    conn.close()

create_tables()
conn_check = get_db()
cur_check = conn_check.cursor()
cur_check.execute('SELECT COUNT(*) FROM questions')
if cur_check.fetchone()[0] == 0:
    insert_sample_questions()
conn_check.close()

# ================= HELPERS =================
def calculate_bot_speed(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT AVG(wpm) FROM results WHERE user_id=?", (user_id,))
    result = cur.fetchone()
    avg = result[0] if result else None
    conn.close()
    return 30 if avg is None else round(avg * 1.1, 2)

def get_weak_keys(missed_keys):
    if not missed_keys:
        return []
    return [k for k, _ in Counter(missed_keys).most_common(3)]

def analyze_performance_ai(wpm, accuracy, weak_keys):
    prompt = f"""You are a professional typing coach. Give concise feedback.
User Stats: WPM={wpm}, Accuracy={accuracy}%, Weak Keys={', '.join(weak_keys) if weak_keys else 'None'}
Respond ONLY with a JSON object (no markdown):
{{"speed_msg":"one sentence about speed","suggestion":"one specific practice tip","practice_text":"8-10 word practice sentence using their weak keys"}}"""
    result = call_gemini(prompt, max_tokens=300)
    if result:
        try:
            clean = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            parsed = json.loads(clean)
            return parsed.get("speed_msg",""), parsed.get("suggestion",""), parsed.get("practice_text","")
        except Exception:
            pass
    # Fallback
    if wpm < 30:
        speed_msg = "Your typing speed is below average. Keep practising!"
    elif wpm < 60:
        speed_msg = "You're at an average pace — keep pushing!"
    else:
        speed_msg = "Excellent speed! You're in top-tier territory."
    suggestion = ("Focus on keys: " + ", ".join(weak_keys)) if weak_keys else "Great accuracy! Now push your speed."
    return speed_msg, suggestion, "Practice makes perfect keep typing consistently"

def get_league(wpm):
    return "Bronze" if wpm < 30 else "Silver" if wpm <= 60 else "Gold"

# ================= XP / STREAK / ACHIEVEMENTS =================
XP_PER_RACE = 10
XP_WIN_BONUS = 15
XP_ACCURACY_BONUS = 10  # if accuracy >= 95

LEVELS = [
    (0,    "Rookie"),
    (100,  "Racer"),
    (300,  "Pro"),
    (600,  "Expert"),
    (1000, "Legend"),
]

BADGES = {
    "first_race":   ("🏁", "First Race",      "Complete your first race"),
    "speed_demon":  ("⚡", "Speed Demon",     "Hit 60+ WPM"),
    "sharpshooter": ("🎯", "Sharpshooter",    "100% accuracy in a race"),
    "streak_3":     ("🔥", "On Fire",         "3-day race streak"),
    "streak_7":     ("🌟", "Week Warrior",    "7-day race streak"),
    "century":      ("💯", "Century",         "Complete 100 races"),
    "gold_league":  ("🥇", "Gold League",     "Reach Gold league"),
}

def get_level(xp):
    level_name = LEVELS[0][1]
    for threshold, name in LEVELS:
        if xp >= threshold:
            level_name = name
    return level_name

def next_level_xp(xp):
    for i, (threshold, _) in enumerate(LEVELS):
        if xp < threshold:
            prev = LEVELS[i-1][0] if i > 0 else 0
            return threshold, prev
    return LEVELS[-1][0], LEVELS[-2][0]

def update_xp_streak(user_id, wpm, accuracy, won):
    from datetime import date
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO user_xp(user_id) VALUES(?)", (user_id,))
    cur.execute("SELECT xp, streak, last_race_date FROM user_xp WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    xp, streak, last_date = row if row else (0, 0, "")
    today = str(date.today())
    from datetime import date as dt, timedelta
    yesterday = str(dt.today() - timedelta(days=1))
    if last_date == today:
        pass  # already raced today, no streak change
    elif last_date == yesterday:
        streak += 1
    else:
        streak = 1
    earned = XP_PER_RACE
    if won: earned += XP_WIN_BONUS
    if float(accuracy) >= 95: earned += XP_ACCURACY_BONUS
    xp += earned
    cur.execute("UPDATE user_xp SET xp=?, streak=?, last_race_date=? WHERE user_id=?",
                (xp, streak, today, user_id))
    # Check achievements
    cur.execute("SELECT badge FROM achievements WHERE user_id=?", (user_id,))
    existing = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT COUNT(*) FROM results WHERE user_id=?", (user_id,))
    race_count = cur.fetchone()[0]
    new_badges = []
    checks = [
        ("first_race",   race_count >= 1),
        ("speed_demon",  float(wpm) >= 60),
        ("sharpshooter", float(accuracy) >= 100),
        ("streak_3",     streak >= 3),
        ("streak_7",     streak >= 7),
        ("century",      race_count >= 100),
        ("gold_league",  float(wpm) > 60),
    ]
    for badge_key, condition in checks:
        if condition and badge_key not in existing:
            cur.execute("INSERT INTO achievements(user_id, badge) VALUES(?,?)", (user_id, badge_key))
            new_badges.append(badge_key)
    conn.commit(); conn.close()
    return xp, streak, earned, new_badges

def get_user_xp_info(user_id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT xp, streak FROM user_xp WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row: return {"xp": 0, "streak": 0, "level": "Rookie", "next_xp": 100, "prev_xp": 0}
    xp, streak = row
    next_xp, prev_xp = next_level_xp(xp)
    return {"xp": xp, "streak": streak, "level": get_level(xp), "next_xp": next_xp, "prev_xp": prev_xp}

def analyze_pattern(timings):
    if not timings:
        return "No data"
    avg = sum(timings) / len(timings)
    return "🐢 Slow rhythm" if avg > 300 else "⚡ Fast rhythm" if avg < 150 else "⚖️ Balanced rhythm"

def detect_fatigue(wpm, accuracy):
    if wpm < 25 or accuracy < 70:
        return "😴 Take a short break!"
    elif wpm < 40 or accuracy < 85:
        return "⚠️ Slight fatigue — stay focused!"
    return "💪 Performing well!"

# ================= AUTH =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (request.form["username"], request.form["password"]))
        conn.commit(); conn.close()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (request.form["username"], request.form["password"]))
        user = cur.fetchone(); conn.close()
        if user:
            session["user_id"] = user[0]
            return redirect("/")
        error = "Invalid username or password. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear(); return redirect("/login")

# ================= ROUTES =================
@app.route("/")
def home():
    if "user_id" not in session: return redirect("/login")
    xp_info = get_user_xp_info(session["user_id"])
    return render_template("index.html", bot_speed=calculate_bot_speed(session["user_id"]), xp_info=xp_info)

@app.route("/get-xp")
def get_xp():
    if "user_id" not in session: return jsonify({})
    return jsonify(get_user_xp_info(session["user_id"]))

@app.route("/get-achievements")
def get_achievements():
    if "user_id" not in session: return jsonify([])
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT badge, earned_at FROM achievements WHERE user_id=? ORDER BY earned_at DESC", (session["user_id"],))
    rows = cur.fetchall(); conn.close()
    result = []
    for badge_key, earned_at in rows:
        if badge_key in BADGES:
            icon, name, desc = BADGES[badge_key]
            result.append({"key": badge_key, "icon": icon, "name": name, "desc": desc, "earned_at": earned_at})
    return jsonify(result)

@app.route("/save-result", methods=["POST"])
def save_result():
    if "user_id" not in session: return jsonify({"error":"Unauthorized"}), 401
    data = request.json
    timings = [float(t) for t in data.get("timings", [])]
    won = data.get("won", False)
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO results(user_id,wpm,accuracy,missed_keys,timings) VALUES(?,?,?,?,?)",
                (session["user_id"], data["wpm"], data["accuracy"], data["missed_keys"], str(timings)))
    conn.commit(); conn.close()
    weak_keys = get_weak_keys(data["missed_keys"])
    feedback, suggestion, practice_text = analyze_performance_ai(float(data["wpm"]), float(data["accuracy"]), weak_keys)
    pattern = analyze_pattern(timings)
    fatigue = detect_fatigue(float(data["wpm"]), float(data["accuracy"]))
    xp, streak, xp_earned, new_badges = update_xp_streak(session["user_id"], data["wpm"], data["accuracy"], won)
    next_xp, prev_xp = next_level_xp(xp)
    badge_data = [{"key": k, "icon": BADGES[k][0], "name": BADGES[k][1], "desc": BADGES[k][2]} for k in new_badges if k in BADGES]
    return jsonify({"league": get_league(float(data["wpm"])), "weak_keys": weak_keys,
                    "feedback": feedback, "suggestion": suggestion, "pattern": pattern,
                    "fatigue": fatigue, "practice_text": practice_text,
                    "xp": xp, "xp_earned": xp_earned, "streak": streak,
                    "level": get_level(xp), "next_xp": next_xp, "prev_xp": prev_xp,
                    "new_badges": badge_data})

@app.route("/leaderboard")
def leaderboard():
    if "user_id" not in session: return redirect("/login")
    conn = get_db(); cur = conn.cursor()
    cur.execute("""SELECT users.username, COUNT(DISTINCT submissions.question_id),
        SUM(CASE WHEN questions.difficulty='Easy' THEN 10 WHEN questions.difficulty='Medium' THEN 20 WHEN questions.difficulty='Hard' THEN 30 ELSE 10 END)
        FROM submissions JOIN users ON users.id=submissions.user_id JOIN questions ON questions.id=submissions.question_id
        WHERE submissions.status='Accepted' GROUP BY users.id,users.username ORDER BY 3 DESC,2 DESC""")
    players = cur.fetchall()
    cur.execute("""SELECT questions.id,questions.title,questions.difficulty,COUNT(DISTINCT submissions.user_id)
        FROM questions LEFT JOIN submissions ON submissions.question_id=questions.id AND submissions.status='Accepted'
        GROUP BY questions.id ORDER BY 4 DESC""")
    all_q = cur.fetchall(); conn.close()
    seen = set(); questions = []
    for q in all_q:
        if q[1] not in seen: seen.add(q[1]); questions.append(q)
    return render_template("leaderboard.html", players=players, questions=questions)

@app.route("/time")
def time_mode(): return render_template("time.html")

@app.route("/challenge")
def challenge_mode(): return render_template("challenge.html")

@app.route("/goal")
def goal_mode(): return render_template("goal.html")

@app.route("/code")
def code():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM questions"); questions = cur.fetchall(); conn.close()
    return render_template("code.html", questions=questions)

@app.route("/profile")
def profile():
    if "user_id" not in session: return redirect("/login")
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE id=?", (session["user_id"],))
    user_row = cur.fetchone(); username = user_row[0] if user_row else "Unknown"
    cur.execute("SELECT wpm,accuracy FROM results WHERE user_id=?", (session["user_id"],))
    data = cur.fetchall()
    cur.execute("""SELECT users.username, RANK() OVER (ORDER BY MAX(results.wpm) DESC), MAX(results.wpm)
        FROM results JOIN users ON results.user_id=users.id GROUP BY users.id,users.username ORDER BY 3 DESC LIMIT 10""")
    lb = cur.fetchall(); conn.close()
    wpms = [r[0] for r in data if r[0]]
    accs = [r[1] for r in data if r[1]]
    avg_wpm = round(sum(wpms)/len(wpms), 1) if wpms else 0
    avg_acc = round(sum(accs)/len(accs), 1) if accs else 0
    games = len(data)
    best_wpm = round(max(wpms), 1) if wpms else 0
    return render_template("profile.html", data=data, username=username, leaderboard=lb,
                           avg_wpm=avg_wpm, avg_acc=avg_acc, games=games, best_wpm=best_wpm)

import subprocess, tempfile

@app.route("/run-code", methods=["POST"])
def run_code():
    data = request.json; user_code = data.get("code",""); question_id = data.get("question_id",1)
    language = data.get("language","python"); temp_file = None
    try:
        conn = get_db(); cur = conn.cursor()
        cur.execute("SELECT sample_input,sample_output FROM questions WHERE id=?", (question_id,))
        q = cur.fetchone(); conn.close()
        if not q: return jsonify({"error":"Question not found"})
        sample_input, expected_output = q[0], q[1].strip()
        if language == "python":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w") as f:
                f.write(user_code); temp_file = f.name
            cmd = ["python", temp_file]
        elif language == "cpp":
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".cpp").name
            exe_file = temp_file.replace(".cpp",".exe")
            with open(temp_file,"w") as f: f.write(user_code)
            cr = subprocess.run(["g++",temp_file,"-o",exe_file], capture_output=True, text=True)
            if cr.returncode != 0: return jsonify({"error":cr.stderr})
            cmd = [exe_file]
        elif language == "java":
            td = tempfile.mkdtemp(); fp = os.path.join(td,"Main.java")
            with open(fp,"w") as f: f.write(user_code)
            cr = subprocess.run(["javac",fp], capture_output=True, text=True)
            if cr.returncode != 0: return jsonify({"error":cr.stderr})
            cmd = ["java","-cp",td,"Main"]
        else:
            return jsonify({"error":"Unsupported language"})
        result = subprocess.run(cmd, input=sample_input, text=True, capture_output=True, timeout=5)
        output = result.stdout.strip()
        status = "Accepted" if output == expected_output else "Wrong Answer"
        conn = get_db(); cur = conn.cursor()
        cur.execute("INSERT INTO submissions(user_id,question_id,code,status) VALUES(?,?,?,?)",
                    (session.get("user_id",1), question_id, user_code, status))
        conn.commit(); conn.close()
        return jsonify({"status":"Accepted ✅" if status=="Accepted" else "Wrong Answer ❌",
                        "results":[f"Input: {sample_input}", f"Expected: {expected_output}", f"Output: {output}"]})
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        if temp_file and os.path.exists(temp_file): os.remove(temp_file)

@app.route("/get-question/<int:id>")
def get_question(id):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE id=?", (id,))
    q = cur.fetchone(); conn.close()
    if not q: return jsonify({"error":"Not found"})
    # Decode double-escaped newlines stored in DB so editor shows real line breaks
    starter = q[7].replace('\\n', '\n') if q[7] else ''
    return jsonify({"id":q[0],"title":q[1],"description":q[2],"starter_code":starter,"difficulty":q[8] if len(q)>8 else ""})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
