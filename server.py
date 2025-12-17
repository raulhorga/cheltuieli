from flask import Flask, request, send_from_directory
import os

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/cheltuieli.csv")
def csv():
    return send_from_directory(BASE, "cheltuieli.csv")

@app.route("/save-csv", methods=["POST"])
def save():
    with open(os.path.join(BASE, "cheltuieli.csv"), "w", encoding="utf-8") as f:
        f.write(request.data.decode("utf-8"))
    return {"ok": True}

app.run(port=8000)
