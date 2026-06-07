"""
Exam Practice App - Flask Backend
Serves the web UI and exposes exam JSON files from the local data directory.
"""
import glob
import json
import os
from pathlib import Path

from flask import Flask, abort, jsonify, render_template

app = Flask(__name__)

# ── Local directory containing exam JSON files ──────────────────────────────
DATA_DIR = r"G:\My Drive\Sync\Docs"


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/exams")
def list_exams():
    """Return metadata for every JSON exam file found in DATA_DIR."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))
    result = []
    for fpath in files:
        try:
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            result.append({
                "filename": os.path.basename(fpath),
                "name": data.get("exam", os.path.basename(fpath)),
                "code": data.get("code", ""),
                "total_questions": data.get("total_questions", 0),
            })
        except Exception:
            pass
    return jsonify(result)


@app.route("/api/exam/<filename>")
def get_exam(filename):
    """Return full exam data for a single JSON file."""
    # Prevent path traversal: accept basename only, must end with .json
    safe_name = Path(filename).name
    if not safe_name.lower().endswith(".json"):
        abort(400, description="Only .json files are allowed.")

    fpath = os.path.join(DATA_DIR, safe_name)
    if not os.path.isfile(fpath):
        abort(404, description="Exam file not found.")

    try:
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as exc:
        abort(500, description=str(exc))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting Exam Practice App at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
