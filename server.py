from flask import Flask, request, send_from_directory, jsonify
import os

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
CSV_NAME = "cheltuieli.csv"

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route(f"/{CSV_NAME}")
def csv_file():
    return send_from_directory(BASE, CSV_NAME)

@app.route("/save-csv", methods=["POST"])
def save_csv():
    data = request.data.decode("utf-8")
    path = os.path.join(BASE, CSV_NAME)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    return jsonify({"ok": True, "path": path, "bytes_written": len(data)})

@app.route("/debug")
def debug():
    path = os.path.join(BASE, CSV_NAME)
    return jsonify({
        "base": BASE,
        "csv_path": path,
        "csv_exists": os.path.exists(path),
        "csv_size": os.path.getsize(path) if os.path.exists(path) else None,
    })

if __name__ == "__main__":
    app.run(port=8000, debug=True)
