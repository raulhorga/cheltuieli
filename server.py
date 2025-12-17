from flask import Flask, request, send_from_directory, jsonify
import os, subprocess, datetime

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

def run(cmd):
    r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/cheltuieli.csv")
def csv_file():
    return send_from_directory(BASE, "cheltuieli.csv")

@app.route("/save-csv", methods=["POST"])
def save_csv():
    csv_path = os.path.join(BASE, "cheltuieli.csv")
    data = request.data.decode("utf-8")

    # 1) suprascrie local
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(data)

    try:
        # 2) commit + push
        run(["git", "add", "cheltuieli.csv"])

        msg = f"Update cheltuieli.csv {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        # dacă nu sunt schimbări, commit va eșua; tratăm elegant:
        try:
            run(["git", "commit", "-m", msg])
        except RuntimeError as e:
            if "nothing to commit" in str(e).lower():
                return jsonify({"ok": True, "note": "No changes to commit."})
            raise

        run(["git", "push"])
        return jsonify({"ok": True})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=8000)
