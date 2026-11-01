"""Class session management component (SAMS-F-013)."""
from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from .auth import role_required
from .db import get_db
from .utils import validate

bp = Blueprint("class_sessions", __name__, url_prefix="/sessions")

TEXT_FIELDS = [
    {"name": "session_date", "label": "Date", "type": "date"},
    {"name": "topic", "label": "Topic", "type": "text", "optional": True},
]


def own_subjects():
    """Subjects assigned to the logged-in faculty member."""
    return get_db().execute(
        "SELECT s.id, s.code, s.name FROM subjects s "
        "JOIN faculty f ON f.id = s.faculty_id "
        "WHERE f.user_id = ? ORDER BY s.code", (g.user["id"],)
    ).fetchall()


def session_fields(subjects):
    options = [(s["id"], f"{s['code']} - {s['name']}") for s in subjects]
    subject_field = {"name": "subject_id", "label": "Subject",
                     "type": "select", "options": options}
    return [subject_field] + TEXT_FIELDS


def subject_choice(form, subjects):
    """The chosen subject id, only if it is one of the faculty member's own."""
    value = form.get("subject_id", "")
    if value.isdigit() and int(value) in {s["id"] for s in subjects}:
        return int(value)
    return None


def get_own_session(record_id):
    """Load a class session owned by the logged-in faculty member, else 404."""
    row = get_db().execute(
        "SELECT cs.*, s.code AS subject_code, s.name AS subject_name "
        "FROM class_sessions cs "
        "JOIN subjects s ON s.id = cs.subject_id "
        "JOIN faculty f ON f.id = s.faculty_id "
        "WHERE cs.id = ? AND f.user_id = ?", (record_id, g.user["id"])
    ).fetchone()
    if row is None:
        abort(404)
    return row


@bp.route("/")
@role_required("faculty")
def index():
    rows = get_db().execute(
        "SELECT cs.id, s.code AS subject_code, cs.session_date, cs.topic "
        "FROM class_sessions cs "
        "JOIN subjects s ON s.id = cs.subject_id "
        "JOIN faculty f ON f.id = s.faculty_id "
        "WHERE f.user_id = ? ORDER BY cs.session_date DESC, cs.id DESC",
        (g.user["id"],)
    ).fetchall()
    return render_template(
        "list.html", title="Class sessions",
        columns=[("subject_code", "Subject"), ("session_date", "Date"),
                 ("topic", "Topic")],
        rows=rows, add_url=url_for("class_sessions.add"),
        edit_endpoint="class_sessions.edit",
        extra_links=[("Attendance", "attendance.record")],
    )


@bp.route("/add", methods=("GET", "POST"))
@role_required("faculty")
def add():
    subjects = own_subjects()
    fields = session_fields(subjects)
    if request.method == "POST":
        errors = validate(request.form, fields)
        subject_id = subject_choice(request.form, subjects)
        if subject_id is None:
            errors.append("Choose one of your assigned subjects.")
        if not errors:
            db = get_db()
            db.execute(
                "INSERT INTO class_sessions (subject_id, session_date, topic) "
                "VALUES (?, ?, ?)",
                (subject_id, request.form["session_date"].strip(),
                 request.form.get("topic", "").strip() or None))
            db.commit()
            flash("Class session created.", "success")
            return redirect(url_for("class_sessions.index"))
        for error in errors:
            flash(error, "error")
    return render_template(
        "form.html", title="Add class session", fields=fields,
        values=request.form, cancel_url=url_for("class_sessions.index"))


@bp.route("/<int:record_id>/edit", methods=("GET", "POST"))
@role_required("faculty")
def edit(record_id):
    class_session = get_own_session(record_id)
    subjects = own_subjects()
    fields = session_fields(subjects)
    if request.method == "POST":
        values = request.form
    else:
        values = {k: ("" if v is None else v) for k, v in dict(class_session).items()}
    if request.method == "POST":
        errors = validate(request.form, fields)
        subject_id = subject_choice(request.form, subjects)
        if subject_id is None:
            errors.append("Choose one of your assigned subjects.")
        if not errors:
            db = get_db()
            db.execute(
                "UPDATE class_sessions SET subject_id = ?, session_date = ?, "
                "topic = ? WHERE id = ?",
                (subject_id, request.form["session_date"].strip(),
                 request.form.get("topic", "").strip() or None, record_id))
            db.commit()
            flash("Class session updated.", "success")
            return redirect(url_for("class_sessions.index"))
        for error in errors:
            flash(error, "error")
    return render_template(
        "form.html", title="Edit class session", fields=fields, values=values,
        cancel_url=url_for("class_sessions.index"))
