import os
import sqlite3
import uuid
from datetime import datetime

from flask import (
    Flask,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
    DATABASE=os.path.join(BASE_DIR, "instance", "journal.db"),
    UPLOAD_FOLDER=os.path.join(BASE_DIR, "uploads"),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with sqlite3.connect(app.config["DATABASE"]) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                body TEXT,
                photo TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    entries = get_db().execute("SELECT * FROM entries ORDER BY id DESC").fetchall()
    return render_template("index.html", entries=entries)


@app.route("/entries", methods=["POST"])
def create_entry():
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    photo = request.files.get("photo")

    photo_name = None
    if photo and photo.filename:
        if not allowed_file(photo.filename):
            flash("Unsupported file type. Use PNG, JPG, GIF, WEBP, or HEIC.")
            return redirect(url_for("index"))
        ext = photo.filename.rsplit(".", 1)[1].lower()
        photo_name = f"{uuid.uuid4().hex}.{ext}"
        photo.save(os.path.join(app.config["UPLOAD_FOLDER"], photo_name))

    if not body and not photo_name:
        flash("Add some text or a photo to save an entry.")
        return redirect(url_for("index"))

    db = get_db()
    db.execute(
        "INSERT INTO entries (title, body, photo, created_at) VALUES (?, ?, ?, ?)",
        (title, body, photo_name, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    db.commit()
    flash("Entry saved.")
    return redirect(url_for("index"))


@app.route("/entries/<int:entry_id>/delete", methods=["POST"])
def delete_entry(entry_id):
    db = get_db()
    entry = db.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    if entry is None:
        abort(404)
    if entry["photo"]:
        path = os.path.join(app.config["UPLOAD_FOLDER"], entry["photo"])
        if os.path.exists(path):
            os.remove(path)
    db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    db.commit()
    flash("Entry deleted.")
    return redirect(url_for("index"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=True)
