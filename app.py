"""
Track That — Job & internship application tracker.
Flask app with SQLite for persistent storage.
"""
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "applications.db"
UPLOAD_FOLDER = APP_DIR / "instance" / "resumes"
ALLOWED_RESUME_EXTENSIONS = {"pdf", "doc", "docx"}
MAX_RESUME_SIZE = 10 * 1024 * 1024  # 10 MB

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["MAX_CONTENT_LENGTH"] = MAX_RESUME_SIZE


def init_db():
    """Create applications table if it doesn't exist and add resume_path if missing."""
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Applied',
                date_applied TEXT NOT NULL,
                job_url TEXT,
                notes TEXT,
                resume_path TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Add resume_path column if missing (migration)
        try:
            conn.execute("ALTER TABLE applications ADD COLUMN resume_path TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row):
    return dict(row) if row else None


def allowed_resume(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_RESUME_EXTENSIONS


def secure_resume_filename(app_id, filename):
    ext = filename.rsplit(".", 1)[1].lower()
    safe = re.sub(r"[^\w.-]", "_", filename.rsplit(".", 1)[0])[:80]
    return f"{app_id}_{safe}.{ext}"


def save_resume(file, app_id):
    """Save uploaded file to UPLOAD_FOLDER. Returns relative path segment for DB, or None on error."""
    if not file or not allowed_resume(file.filename):
        return None
    path = UPLOAD_FOLDER / secure_resume_filename(app_id, file.filename)
    file.save(path)
    return path.name


def get_resume_path(resume_path):
    """Return full Path for a stored resume filename, or None."""
    if not resume_path:
        return None
    p = UPLOAD_FOLDER / resume_path
    return p if p.is_file() else None


STATUSES = [
    "Applied",
    "Interviewing",
    "Offer",
    "Rejected",
    "Withdrawn",
    "Accepted",
]


# ----- Page routes -----

@app.route("/")
def index():
    return redirect(url_for("list_applications"))


@app.route("/applications")
def list_applications():
    return render_template("list.html", statuses=STATUSES)


@app.route("/applications/add")
def add_page():
    return render_template("add.html", statuses=STATUSES)


@app.route("/applications/<int:app_id>/edit")
def edit_page(app_id):
    return render_template("edit.html", app_id=app_id, statuses=STATUSES)


# ----- API routes -----

@app.route("/api/applications", methods=["GET"])
def api_list():
    status_filter = request.args.get("status", "").strip()
    search = request.args.get("q", "").strip()
    with get_db() as conn:
        if status_filter and search:
            pattern = f"%{search}%"
            rows = conn.execute(
                """SELECT * FROM applications
                   WHERE status = ? AND (
                       company_name LIKE ? OR role LIKE ? OR
                       status LIKE ? OR COALESCE(notes, '') LIKE ?
                   )
                   ORDER BY date_applied DESC, id DESC""",
                (status_filter, pattern, pattern, pattern, pattern),
            ).fetchall()
        elif status_filter:
            rows = conn.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY date_applied DESC, id DESC",
                (status_filter,),
            ).fetchall()
        elif search:
            pattern = f"%{search}%"
            rows = conn.execute(
                """SELECT * FROM applications
                   WHERE company_name LIKE ? OR role LIKE ? OR status LIKE ? OR COALESCE(notes, '') LIKE ?
                   ORDER BY date_applied DESC, id DESC""",
                (pattern, pattern, pattern, pattern),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM applications ORDER BY date_applied DESC, id DESC"
            ).fetchall()
        applications = [row_to_dict(r) for r in rows]
    return jsonify(applications)


@app.route("/api/applications/<int:app_id>", methods=["GET"])
def api_get(app_id):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    if not row:
        return jsonify({"error": "Not found"}), 404
    return jsonify(row_to_dict(row))


def _parse_application_data():
    """Parse application fields from either JSON or form data."""
    if request.content_type and "multipart/form-data" in request.content_type:
        data = request.form
    else:
        data = request.get_json() or {}
    return {
        "company_name": (data.get("company_name") or "").strip(),
        "role": (data.get("role") or "").strip(),
        "status": (data.get("status") or "Applied").strip() or "Applied",
        "date_applied": (data.get("date_applied") or "").strip(),
        "job_url": (data.get("job_url") or "").strip() or None,
        "notes": (data.get("notes") or "").strip() or None,
    }


@app.route("/api/applications", methods=["POST"])
def api_create():
    data = _parse_application_data()
    company_name = data["company_name"]
    role = data["role"]
    status = data["status"] if data["status"] in STATUSES else "Applied"
    date_applied = data["date_applied"]
    job_url = data["job_url"]
    notes = data["notes"]

    if not company_name or not role or not date_applied:
        return jsonify({"error": "company_name, role, and date_applied are required"}), 400

    now = datetime.utcnow().isoformat() + "Z"
    resume_path = None
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO applications
               (company_name, role, status, date_applied, job_url, notes, resume_path, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (company_name, role, status, date_applied, job_url, notes, resume_path, now, now),
        )
        app_id = cur.lastrowid

    file = request.files.get("resume") if request.files else None
    if file and file.filename and allowed_resume(file.filename):
        if file.content_length and file.content_length > MAX_RESUME_SIZE:
            return jsonify({"error": "Resume file too large (max 10 MB)"}), 400
        resume_path = save_resume(file, app_id)
        if resume_path:
            with get_db() as conn:
                conn.execute("UPDATE applications SET resume_path = ? WHERE id = ?", (resume_path, app_id))

    return jsonify({"id": app_id, "message": "Created"}), 201


@app.route("/api/applications/<int:app_id>", methods=["PUT"])
def api_update(app_id):
    data = _parse_application_data()
    company_name = data["company_name"]
    role = data["role"]
    status = data["status"] if data["status"] in STATUSES else "Applied"
    date_applied = data["date_applied"]
    job_url = data["job_url"]
    notes = data["notes"]

    if not company_name or not role or not date_applied:
        return jsonify({"error": "company_name, role, and date_applied are required"}), 400

    remove_resume = False
    if request.content_type and "multipart/form-data" in request.content_type:
        remove_resume = request.form.get("remove_resume") == "1"

    with get_db() as conn:
        row = conn.execute("SELECT resume_path FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        old_resume_path = row["resume_path"]

    resume_path = old_resume_path
    if remove_resume and old_resume_path:
        full = get_resume_path(old_resume_path)
        if full and full.exists():
            full.unlink(missing_ok=True)
        resume_path = None
    else:
        file = request.files.get("resume") if request.files else None
        if file and file.filename and allowed_resume(file.filename):
            if file.content_length and file.content_length > MAX_RESUME_SIZE:
                return jsonify({"error": "Resume file too large (max 10 MB)"}), 400
            if old_resume_path:
                old_full = get_resume_path(old_resume_path)
                if old_full and old_full.exists():
                    old_full.unlink(missing_ok=True)
            resume_path = save_resume(file, app_id)

    now = datetime.utcnow().isoformat() + "Z"
    with get_db() as conn:
        cur = conn.execute(
            """UPDATE applications SET
               company_name = ?, role = ?, status = ?, date_applied = ?, job_url = ?, notes = ?, resume_path = ?, updated_at = ?
               WHERE id = ?""",
            (company_name, role, status, date_applied, job_url, notes, resume_path, now, app_id),
        )
        if cur.rowcount == 0:
            return jsonify({"error": "Not found"}), 404
    return jsonify({"message": "Updated"})


@app.route("/api/applications/<int:app_id>", methods=["DELETE"])
def api_delete(app_id):
    with get_db() as conn:
        row = conn.execute("SELECT resume_path FROM applications WHERE id = ?", (app_id,)).fetchone()
        if not row:
            return jsonify({"error": "Not found"}), 404
        resume_path = row["resume_path"]
        conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    if resume_path:
        full = get_resume_path(resume_path)
        if full and full.exists():
            full.unlink(missing_ok=True)
    return jsonify({"message": "Deleted"})


@app.route("/api/applications/<int:app_id>/resume")
def api_resume_download(app_id):
    with get_db() as conn:
        row = conn.execute("SELECT resume_path FROM applications WHERE id = ?", (app_id,)).fetchone()
    if not row or not row["resume_path"]:
        return jsonify({"error": "No resume"}), 404
    full = get_resume_path(row["resume_path"])
    if not full:
        return jsonify({"error": "File not found"}), 404
    return send_file(full, as_attachment=True, download_name=row["resume_path"])


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5001)
