from flask import Flask, render_template, request, redirect, session
import sqlite3, random, os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT,
                    password TEXT
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS passengers (
                    pnr INTEGER,
                    name TEXT,
                    status TEXT,
                    seat TEXT
                )''')

    conn.commit()
    conn.close()

init_db()

# ---------- FUNCTIONS ----------
def generate_pnr():
    return random.randint(100000, 999999)

def book_ticket(name):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM passengers WHERE status='CONFIRMED'")
    confirmed = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM passengers WHERE status='RAC'")
    rac = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM passengers WHERE status='WAITING'")
    waiting = c.fetchone()[0]

    pnr = generate_pnr()

    if confirmed < 2:
        seat = f"S{confirmed+1}"
        status = "CONFIRMED"
    elif rac < 2:
        seat = "RAC"
        status = "RAC"
    elif waiting < 2:
        seat = "WL"
        status = "WAITING"
    else:
        return "No Tickets Available"

    c.execute("INSERT INTO passengers VALUES (?, ?, ?, ?)",
              (pnr, name, status, seat))

    conn.commit()
    conn.close()

    return f"{name} booked | {status} | PNR: {pnr}"

def cancel_ticket(pnr):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM passengers WHERE pnr=?", (pnr,))
    conn.commit()
    conn.close()

    return "Ticket Cancelled"

def get_data():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM passengers")
    data = c.fetchall()
    conn.close()
    return data

# ---------- ROUTES ----------
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (user,pwd))
        result = c.fetchone()
        conn.close()

        if result:
            session["user"] = user
            return redirect("/dashboard")
        else:
            return "Invalid Login"

    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?,?)", (user,pwd))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    message = ""

    if request.method == "POST":
        action = request.form["action"]

        if action == "book":
            name = request.form["name"]
            message = book_ticket(name)

        elif action == "cancel":
            pnr = int(request.form["pnr"])
            message = cancel_ticket(pnr)

    data = get_data()
    return render_template("dashboard.html", data=data, message=message)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
