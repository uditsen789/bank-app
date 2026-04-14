from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# -------- DATABASE --------
conn = sqlite3.connect("bank.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT,
    password TEXT,
    balance INTEGER
)
""")
conn.commit()

# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")

# -------- SIGNUP --------
@app.route("/signup", methods=["POST"])
def signup():
    u = request.form["username"]
    p = request.form["password"]

    cursor.execute("INSERT INTO users VALUES (?, ?, ?)", (u, p, 0))
    conn.commit()

    return redirect("/")

# -------- LOGIN --------
@app.route("/login", methods=["POST"])
def login():
    u = request.form["username"]
    p = request.form["password"]

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    user = cursor.fetchone()

    if user:
        return redirect("/dashboard?user=" + u)
    return "Invalid Login"

# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    u = request.args.get("user")

    cursor.execute("SELECT balance FROM users WHERE username=?", (u,))
    bal = cursor.fetchone()[0]

    return render_template("dashboard.html", user=u, balance=bal)

# -------- DEPOSIT --------
@app.route("/deposit", methods=["POST"])
def deposit():
    u = request.form["user"]
    amt = int(request.form["amount"])

    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, u))
    conn.commit()

    return redirect("/dashboard?user=" + u)

# -------- WITHDRAW --------
@app.route("/withdraw", methods=["POST"])
def withdraw():
    u = request.form["user"]
    amt = int(request.form["amount"])

    cursor.execute("SELECT balance FROM users WHERE username=?", (u,))
    bal = cursor.fetchone()[0]

    if bal >= amt:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, u))
        conn.commit()
        

    return redirect("/dashboard?user=" + u)

