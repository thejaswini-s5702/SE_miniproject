"""Subject management component (SAMS-F-011)."""
from sqlite3 import IntegrityError

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .auth import role_required
from .db import get_db
from .utils import validate

bp = Blueprint("subjects", __name__, url_prefix="/subjects")

TEXT_FIELDS = [
    {"name": "code", "label": "Subject code", "type": "text"},
    {"name": "name", "label": "Subject name", "type": "text"},
]


def subject_fields():
    """Form fields, with the faculty dropdown filled from the database."""
    members = get_db().execute(
        "SELECT id, name, employee_id FROM faculty ORDER BY name").fetchall()
    options = [(m["id"], f"{m['name']} ({m['employee_id']})") for m in members]
    return TEXT_FIELDS + [{
        "name": "faculty_id", "label": "Assigned faculty",
        "type": "select", "options": options,
    }]


def faculty_value(form):
    value = form.get("faculty_id", "").strip()
    return int(value) if value.isdigit() else None


@bp.route("/")
@role_required("admin")
def index():
    rows = get_db().execute(
        "SELECT s.id, s.code, s.name, f.name AS faculty_name FROM subjects s "
        "LEFT JOIN faculty f ON f.id = s.faculty_id ORDER BY s.code"
    ).fetchall()
    return render_template(
        "list.html", title="Subjects",
        columns=[("code", "Code"), ("name", "Subject"),
                 ("faculty_name", "Assigned faculty")],
        rows=rows, add_url=url_for("subjects.add"), edit_endpoint="subjects.edit")


@bp.route("/add", methods=("GET", "POST"))
@role_required("admin")
def add():
    fields = subject_fields()
    if request.method == "POST":
        errors = validate(request.form, fields)
        if not errors:
            db = get_db()
            try:
                db.execute(
                    "INSERT INTO subjects (code, name, faculty_id) VALUES (?, ?, ?)",
                    (request.form["code"].strip(), request.form["name"].strip(),
                     faculty_value(request.form)))
                db.commit()
                flash("Subject added.", "success")
                return redirect(url_for("subjects.index"))
            except IntegrityError:
                db.rollback()
                errors.append("Subject code already exists or faculty is invalid.")
        for error in errors:
            flash(error, "error")
    return render_template(
        "form.html", title="Add subject", fields=fields, values=request.form,
        cancel_url=url_for("subjects.index"))


@bp.route("/<int:record_id>/edit", methods=("GET", "POST"))
@role_required("admin")
def edit(record_id):
    db = get_db()
    subject = db.execute(
        "SELECT * FROM subjects WHERE id = ?", (record_id,)).fetchone()
    if subject is None:
        abort(404)
    fields = subject_fields()
    values = request.form if request.method == "POST" else dict(subject)
    if request.method == "POST":
        errors = validate(request.form, fields)
        if not errors:
            try:
                db.execute(
                    "UPDATE subjects SET code = ?, name = ?, faculty_id = ? "
                    "WHERE id = ?",
                    (request.form["code"].strip(), request.form["name"].strip(),
                     faculty_value(request.form), record_id))
                db.commit()
                flash("Subject updated.", "success")
                return redirect(url_for("subjects.index"))
            except IntegrityError:
                db.rollback()
                errors.append("Subject code already exists or faculty is invalid.")
        for error in errors:
            flash(error, "error")
    return render_template(
        "form.html", title="Edit subject", fields=fields, values=values,
        cancel_url=url_for("subjects.index"))
