"""
Exam Practice App - Flask Backend
Serves the web UI and exposes exam JSON files from the local data directory.
"""
import glob
import json
import os
from pathlib import Path

try:
    from flask import Flask, abort, jsonify, render_template
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing Flask dependency (or one of its required packages).\n"
        "Install dependencies with one of these commands:\n"
        "  python -m pip install -r requirements.txt\n"
        "  python -m pip install Flask"
    ) from exc

app = Flask(__name__)

# ── Local directory containing exam JSON files ──────────────────────────────
# Override with DATA_DIR environment variable when needed (e.g. different machines).
# Default to the 'resources' folder in the project directory
_default_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
DATA_DIR = os.environ.get("DATA_DIR", _default_dir)


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
    # Cloud Run provides PORT via environment variable
    port = int(os.environ.get("PORT", 5001))
    # Use 0.0.0.0 to make the app accessible externally (required for Cloud Run)
    host = "0.0.0.0"
    print(f"Starting Exam Practice App at http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
