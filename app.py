from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE =================
def get_db():
    return sqlite3.connect("database.db")

def init_db():
    db = get_db()
    cursor = db.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            condition TEXT,
            type TEXT,
            time TEXT,
            status TEXT DEFAULT 'Waiting'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT
        )
    ''')

    cursor.execute("SELECT * FROM admin")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admin VALUES (1, 'admin', 'admin')")

    db.commit()
    db.close()

init_db()

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        )

        if cursor.fetchone():
            session["admin"] = username
            return redirect("/dashboard")

    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "admin" not in session:
        return redirect("/")

    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        condition = request.form.get("condition")
        ptype = request.form.get("type")  # EMERGENCY DROPDOWN

        cursor.execute(
            "INSERT INTO patients (name, condition, type, time, status) VALUES (?, ?, ?, ?, ?)",
            (name, condition, ptype, datetime.now().strftime("%H:%M:%S"), "Waiting")
        )
        db.commit()

    return render_template("dashboard.html", doctor="Dr. Ahmed")

# ================= REAL-TIME API =================
@app.route("/api/patients")
def api_patients():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT * FROM patients
        ORDER BY CASE WHEN type='Emergency' THEN 0 ELSE 1 END, id ASC
    """)

    data = cursor.fetchall()

    result = []
    for i, p in enumerate(data):
        result.append({
            "id": p[0],
            "name": p[1],
            "condition": p[2],
            "type": p[3],
            "time": p[4],
            "status": p[5],
            "position": i + 1,
            "waiting": i * 5
        })

    return jsonify({"patients": result})

# ================= CALL NEXT PATIENT =================
@app.route("/next_patient")
def next_patient():
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id FROM patients
        WHERE status='Waiting'
        ORDER BY CASE WHEN type='Emergency' THEN 0 ELSE 1 END, id ASC
        LIMIT 1
    """)

    patient = cursor.fetchone()

    if patient:
        cursor.execute(
            "UPDATE patients SET status='In Consultation' WHERE id=?",
            (patient[0],)
        )
        db.commit()

    return redirect("/dashboard")

# ================= ONLINE BOOKING =================
@app.route("/book", methods=["GET", "POST"])
def book():
    db = get_db()
    cursor = db.cursor()

    if request.method == "POST":
        name = request.form.get("name")
        condition = request.form.get("condition")
        ptype = request.form.get("type")  # DROPDOWN

        cursor.execute(
            "INSERT INTO patients (name, condition, type, time, status) VALUES (?, ?, ?, ?, ?)",
            (name, condition, ptype, datetime.now().strftime("%H:%M:%S"), "Waiting")
        )
        db.commit()

        cursor.execute("SELECT COUNT(*) FROM patients")
        queue = cursor.fetchone()[0]

        return render_template("success.html", name=name, queue=queue, type=ptype)

    return render_template("book.html")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)