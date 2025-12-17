from flask import Flask, request, jsonify, send_from_directory
import os, sqlite3
from datetime import datetime

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "cheltuieli.sqlite")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,            -- YYYY-MM-DD
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        comment TEXT,
        created_at TEXT NOT NULL       -- ISO timestamp
    );
    """)
    cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);")
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/api/expenses", methods=["GET"])
def list_expenses():
    date_from = request.args.get("from")
    date_to = request.args.get("to")

    q = "SELECT id, date, category, amount, comment, created_at FROM expenses"
    params = []
    where = []
    if date_from:
        where.append("date >= ?")
        params.append(date_from)
    if date_to:
        where.append("date <= ?")
        params.append(date_to)
    if where:
        q += " WHERE " + " AND ".join(where)
    q += " ORDER BY date ASC, id ASC"

    conn = get_conn()
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/categories", methods=["GET"])
def categories():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT category FROM expenses ORDER BY category ASC").fetchall()
    conn.close()
    return jsonify([r["category"] for r in rows])

@app.route("/api/expenses", methods=["POST"])
def add_expense():
    data = request.get_json(force=True, silent=False)
    date = (data.get("date") or "").strip()
    category = (data.get("category") or "").strip()
    amount = data.get("amount")
    comment = (data.get("comment") or "").strip()

    if not date or len(date) != 10:
        return jsonify({"ok": False, "error": "date invalid (YYYY-MM-DD)"}), 400
    if not category:
        return jsonify({"ok": False, "error": "category missing"}), 400
    try:
        amount = float(amount)
    except Exception:
        return jsonify({"ok": False, "error": "amount invalid"}), 400
    if amount <= 0:
        return jsonify({"ok": False, "error": "amount must be > 0"}), 400

    created_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses(date, category, amount, comment, created_at) VALUES(?,?,?,?,?)",
        (date, category, amount, comment, created_at)
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({"ok": True, "id": new_id})

@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    changed = cur.rowcount
    conn.close()
    return jsonify({"ok": True, "deleted": changed})

@app.route("/debug")
def debug():
    exists = os.path.exists(DB_PATH)
    size = os.path.getsize(DB_PATH) if exists else None
    return jsonify({"base": BASE, "db_path": DB_PATH, "db_exists": exists, "db_size": size})

if __name__ == "__main__":
    init_db()
    app.run(port=8000, debug=True)
