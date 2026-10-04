import os, sqlite3, secrets
from flask import Flask, render_template, request, redirect, url_for, abort, jsonify, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-key")

DB = os.environ.get("DATABASE_PATH", "tests.db")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""CREATE TABLE IF NOT EXISTS tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        test_url TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        student_name TEXT NOT NULL,
        score REAL,
        correct INTEGER,
        wrong INTEGER,
        time_taken INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(test_id) REFERENCES tests(id)
    )""")
    con.commit()
    con.close()

@app.before_request
def startup():
    init_db()

def admin_required():
    return session.get("admin") is True

@app.route("/")
def home():
    return redirect(url_for("admin"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not admin_required():
        return redirect(url_for("login"))
    con = db()
    tests = con.execute("SELECT * FROM tests ORDER BY id DESC").fetchall()
    con.close()
    return render_template("admin.html", tests=tests)

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin"))
        error = "Wrong password"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/create", methods=["POST"])
def create_test():
    if not admin_required():
        abort(403)
    name = request.form.get("name", "").strip()
    test_url = request.form.get("test_url", "").strip()
    if not name or not test_url.startswith(("https://", "http://")):
        return "Valid test name and URL required", 400

    slug = secrets.token_urlsafe(7).replace("-", "").replace("_", "")[:10]
    con = db()
    while con.execute("SELECT 1 FROM tests WHERE slug=?", (slug,)).fetchone():
        slug = secrets.token_urlsafe(7)[:10]
    con.execute("INSERT INTO tests(slug,name,test_url) VALUES(?,?,?)",
                (slug, name, test_url))
    con.commit()
    con.close()
    return redirect(url_for("admin"))

@app.route("/test/<slug>", methods=["GET"])
def public_test(slug):
    con = db()
    test = con.execute("SELECT * FROM tests WHERE slug=?", (slug,)).fetchone()
    con.close()
    if not test:
        abort(404)
    return render_template("test.html", test=test)

@app.route("/api/results", methods=["POST"])
def save_result():
    data = request.get_json(silent=True) or {}
    slug = data.get("slug")
    name = str(data.get("student_name", "")).strip()
    if not slug or not name:
        return jsonify({"ok": False, "error": "slug and student_name required"}), 400

    con = db()
    test = con.execute("SELECT id FROM tests WHERE slug=?", (slug,)).fetchone()
    if not test:
        con.close()
        return jsonify({"ok": False, "error": "test not found"}), 404

    con.execute("""INSERT INTO results
        (test_id,student_name,score,correct,wrong,time_taken)
        VALUES (?,?,?,?,?,?)""",
        (test["id"], name, data.get("score"), data.get("correct"),
         data.get("wrong"), data.get("time_taken")))
    con.commit()
    con.close()
    return jsonify({"ok": True})

@app.route("/admin/results/<slug>")
def results(slug):
    if not admin_required():
        return redirect(url_for("login"))
    con = db()
    test = con.execute("SELECT * FROM tests WHERE slug=?", (slug,)).fetchone()
    if not test:
        abort(404)
    rows = con.execute("""SELECT * FROM results WHERE test_id=?
                          ORDER BY score DESC, time_taken ASC, id ASC LIMIT 10""",
                       (test["id"],)).fetchall()
    con.close()
    return render_template("results.html", test=test, rows=rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
