from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, random, smtplib
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

EMAIL = "senudit8761@gmail.com"
PASSWORD = "jdeb scnz qrqy yucn"

# -------- DB INIT --------
def init_db():
    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT UNIQUE,
        password TEXT,
        name TEXT,
        age INTEGER,
        gender TEXT,
        account_number TEXT,
        balance INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        username TEXT,
        type TEXT,
        amount INTEGER,
        account TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

conn = sqlite3.connect("bank.db", check_same_thread=False)
cursor = conn.cursor()

# -------- FUNCTIONS --------
def generate_account():
    return str(random.randint(1000000000, 9999999999))

def current_time():
    return datetime.now().strftime("%d-%m-%Y %I:%M %p")

# 🔥 OTP WITH FALLBACK
def send_otp(receiver_email, otp):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(EMAIL, PASSWORD)

        message = f"Subject: OTP Verification\n\nYour OTP is {otp}"
        server.sendmail(EMAIL, receiver_email, message)

        server.quit()
        print("OTP sent to email ✅")
        return True

    except Exception as e:
        print("EMAIL FAILED ❌:", e)
        print("OTP:", otp)
        return False

# -------- ROUTES --------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def signup():
    email = request.form["username"].strip()

    cursor.execute("SELECT * FROM users WHERE username=?", (email,))
    if cursor.fetchone():
        flash("Account already exists ❌")
        return redirect("/")

    session["temp_user"] = request.form

    otp = str(random.randint(1000, 9999))
    session["otp"] = otp

    sent = send_otp(email, otp)

    if not sent:
        flash(f"Email failed ❌ Use this OTP: {otp}")

    return render_template("verify.html")

@app.route("/verify", methods=["POST"])
def verify():
    if request.form["otp"] == session.get("otp"):
        data = session.get("temp_user")

        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)", (
            data["username"],
            data["password"],
            data["name"],
            data["age"],
            data["gender"],
            generate_account(),
            0
        ))

        conn.commit()
        flash("Account Created ✅")
        return redirect("/")

    return "Wrong OTP ❌"

@app.route("/login", methods=["POST"])
def login():
    u = request.form["username"].strip()
    p = request.form["password"].strip()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    if cursor.fetchone():
        return redirect(f"/dashboard?user={u}")

    return "Login Failed ❌"

@app.route("/dashboard")
def dashboard():
    u = request.args.get("user")

    cursor.execute("SELECT name, age, gender, account_number, balance FROM users WHERE username=?", (u,))
    data = cursor.fetchone()

    cursor.execute("""
    SELECT type, amount, account, time 
    FROM transactions 
    WHERE username=? 
    ORDER BY rowid DESC
    """, (u,))
    transactions = cursor.fetchall()

    return render_template("dashboard.html", user=u, data=data, transactions=transactions)

@app.route("/deposit", methods=["POST"])
def deposit():
    u = request.form["user"]
    amt = int(request.form["amount"])

    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, u))
    cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                   (u, "Deposit", amt, "Self", current_time()))

    conn.commit()
    return redirect(f"/dashboard?user={u}")

@app.route("/withdraw", methods=["POST"])
def withdraw():
    u = request.form["user"]
    amt = int(request.form["amount"])

    cursor.execute("SELECT balance FROM users WHERE username=?", (u,))
    bal = cursor.fetchone()[0]

    if bal >= amt:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, u))
        cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                       (u, "Withdraw", amt, "Self", current_time()))
        conn.commit()

    return redirect(f"/dashboard?user={u}")

@app.route("/transfer", methods=["POST"])
def transfer():
    sender = request.form["user"]
    acc = request.form["account"]
    amt = int(request.form["amount"])

    cursor.execute("SELECT balance FROM users WHERE username=?", (sender,))
    bal = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
    receiver = cursor.fetchone()

    if receiver and bal >= amt:
        cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, sender))
        cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number=?", (amt, acc))

        cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                       (sender, "Transfer", amt, acc, current_time()))

        conn.commit()

    return redirect(f"/dashboard?user={sender}")

@app.route("/logout")
def logout():
    return redirect("/")

if __name__ == "__main__":
    app.run()
