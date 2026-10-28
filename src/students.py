"""Student management component (SAMS-F-004 to F-007)."""
from sqlite3 import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import role_required
from .db import get_db
from .utils import create_user, validate

bp = Blueprint("students", __name__, url_prefix="/students")

PROFILE_FIELDS = [
    {"name": "roll_no", "label": "SRN", "type": "text"},
    {"name": "name", "label": "Full name", "type": "text"},
    {"name": "email", "label": "Email", "type": "email"},
    {"name": "semester", "label": "Semester", "type": "number"},
]
ACCOUNT_FIELDS = [
    {"name": "username", "label": "Username", "type": "text"},
    {"name": "password", "label": "Password", "type": "password"},
]
COLUMNS = [("roll_no", "SRN"), ("name", "Name"), ("email", "Email"),
           ("semester", "Semester")]


@bp.route("/")
@role_required("admin")
def index():
    rows = get_db().execute(
        "SELECT id, roll_no, name, email, semester FROM students ORDER BY roll_no"
    ).fetchall()
    return render_template(
        "list.html", title="Students", columns=COLUMNS, rows=rows,
        add_url=url_for("students.add"),
    )


@bp.route("/add", methods=("GET", "POST"))
@role_required("admin")  # only admins may add students
def add():
    fields = ACCOUNT_FIELDS + PROFILE_FIELDS
    if request.method == "POST":
        errors = validate(request.form, fields)
        if not errors:
            db = get_db()
            try:
                user_id = create_user(
                    db, request.form["username"].strip(),
                    request.form["password"], "student")
                db.execute(
                    "INSERT INTO students (user_id, roll_no, name, email, semester) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, request.form["roll_no"].strip(),
                     request.form["name"].strip(), request.form["email"].strip(),
                     int(request.form["semester"])))
                db.commit()
                flash("Student added.", "success")
                return redirect(url_for("students.index"))
            except IntegrityError:
                db.rollback()
                errors.append("Username or SRN already exists.")
        for error in errors:
            flash(error, "error")
    return render_template(
        "form.html", title="Add student", fields=fields, values=request.form,
        cancel_url=url_for("students.index"))
