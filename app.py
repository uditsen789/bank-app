from flask import Flask, render_template, request, redirect, session, flash
import sqlite3, random, smtplib, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

EMAIL = "senudit8761@gmail.com"
PASSWORD = "jdeb scnz qrqy yucn"

# -------- DB INIT --------
def init_db():
    @app.before_request
    def before_request():
    init_db()
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

# -------- DB CONNECT --------
conn = sqlite3.connect("bank.db", check_same_thread=False)
cursor = conn.cursor()

# -------- FUNCTIONS --------
def generate_account():
    return str(random.randint(1000000000, 9999999999))

def current_time():
    return datetime.now().strftime("%d-%m-%Y %I:%M %p")

def send_otp(receiver_email, otp):
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        message = f"Subject: OTP\n\nYour OTP is {otp}"
        server.sendmail(EMAIL, receiver_email, message)
        server.quit()
        print("OTP:", otp)
    except Exception as e:
        print("EMAIL ERROR:", e)

# -------- HOME --------
@app.route("/")
def home():
    return render_template("index.html")

# -------- SIGNUP --------
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

    send_otp(email, otp)

    return render_template("verify.html")

# -------- VERIFY --------
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

# -------- LOGIN --------
@app.route("/login", methods=["POST"])
def login():
    u = request.form["username"].strip()
    p = request.form["password"].strip()

    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    if cursor.fetchone():
        return redirect(f"/dashboard?user={u}")

    return "Login Failed ❌"

# -------- DASHBOARD --------
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

# -------- DEPOSIT --------
@app.route("/deposit", methods=["POST"])
def deposit():
    u = request.form["user"]
    amt = int(request.form["amount"])

    cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amt, u))
    cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                   (u, "Deposit", amt, "Self", current_time()))

    conn.commit()
    flash("Deposit Successful ✅")

    return redirect(f"/dashboard?user={u}")

# -------- WITHDRAW --------
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
        flash("Withdraw Successful ✅")
    else:
        flash("Insufficient Balance ❌")

    return redirect(f"/dashboard?user={u}")

# -------- TRANSFER --------
@app.route("/transfer", methods=["POST"])
def transfer():
    sender = request.form["user"]
    acc = request.form["account"]
    amt = int(request.form["amount"])

    cursor.execute("SELECT balance FROM users WHERE username=?", (sender,))
    bal = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM users WHERE account_number=?", (acc,))
    receiver = cursor.fetchone()

    if not receiver:
        flash("Receiver not found ❌")
        return redirect(f"/dashboard?user={sender}")

    if bal < amt:
        flash("Insufficient Balance ❌")
        return redirect(f"/dashboard?user={sender}")

    cursor.execute("UPDATE users SET balance = balance - ? WHERE username=?", (amt, sender))
    cursor.execute("UPDATE users SET balance = balance + ? WHERE account_number=?", (amt, acc))

    cursor.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?)",
                   (sender, "Transfer", amt, acc, current_time()))

    conn.commit()
    flash("Transfer Successful ✅")

    return redirect(f"/dashboard?user={sender}")

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    return redirect("/")

# -------- ADMIN --------
@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "1234":
            session["admin"] = True
            return redirect("/admin_panel")
        return "Wrong admin ❌"

    return render_template("admin_login.html")

@app.route("/admin_panel")
def admin_panel():
    if not session.get("admin"):
        return "Access denied ❌"

    cursor.execute("SELECT name, account_number, balance FROM users")
    data = cursor.fetchall()

    return render_template("admin.html", data=data)

# -------- RUN --------
if __name__ == "__main__":
    app.run()
