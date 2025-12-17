from flask import Flask, request, send_from_directory, jsonify
import os, subprocess, datetime

app = Flask(__name__)

# IMPORTANT: repo root = folderul unde e acest server.py (mută server.py în root-ul repo-ului!)
BASE = os.path.dirname(os.path.abspath(__file__))

def run(cmd, cwd=BASE):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return {
        "cmd": " ".join(cmd),
        "cwd": cwd,
        "code": p.returncode,
        "stdout": (p.stdout or "").strip(),
        "stderr": (p.stderr or "").strip(),
    }

def ensure_git_repo():
    # Verifică dacă suntem într-un repo git
    r = run(["git", "rev-parse", "--show-toplevel"])
    if r["code"] != 0:
        return None, r
    repo_root = r["stdout"].strip()
    return repo_root, r

@app.route("/")
def index():
    return send_from_directory(BASE, "index.html")

@app.route("/cheltuieli.csv")
def csv_file():
    return send_from_directory(BASE, "cheltuieli.csv")

@app.route("/debug")
def debug():
    repo_root, git_check = ensure_git_repo()
    info = {
        "BASE": BASE,
        "csv_path": os.path.join(BASE, "cheltuieli.csv"),
        "is_git_repo": repo_root is not None,
        "repo_root": repo_root,
        "git_check": git_check,
        "status": run(["git", "status", "--porcelain"]) if repo_root else None,
        "remote": run(["git", "remote", "-v"]) if repo_root else None,
        "branch": run(["git", "branch", "--show-current"]) if repo_root else None,
    }
    return jsonify(info)

@app.route("/save-csv", methods=["POST"])
def save_csv():
    # 1) scrie CSV local
    csv_path = os.path.join(BASE, "cheltuieli.csv")
    data = request.data.decode("utf-8")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(data)

    # 2) încearcă git add/commit/push
    repo_root, git_check = ensure_git_repo()
    if not repo_root:
        return jsonify({
            "ok": False,
            "where": "ensure_git_repo",
            "hint": "Nu e repo git (nu găsesc .git). Mută server.py în root-ul repo-ului sau rulează din folderul repo-ului.",
            "details": git_check
        }), 500

    results = []
    results.append(run(["git", "add", "cheltuieli.csv"], cwd=repo_root))

    msg = f"Update cheltuieli.csv {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    commit_res = run(["git", "commit", "-m", msg], cwd=repo_root)
    results.append(commit_res)

    # dacă nu a fost nimic de comis, nu mai dăm push
    if commit_res["code"] != 0 and ("nothing to commit" in (commit_res["stdout"] + commit_res["stderr"]).lower()):
        return jsonify({"ok": True, "note": "Nu erau schimbări de comis.", "results": results})

    results.append(run(["git", "push"], cwd=repo_root))

    ok = all(r["code"] == 0 for r in results if r is not None)
    return jsonify({"ok": ok, "results": results}), (200 if ok else 500)

if __name__ == "__main__":
    app.run(port=8000, debug=True)
