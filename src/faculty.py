"""Faculty management component (SAMS-F-008 to F-010)."""
from sqlite3 import IntegrityError

from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from .auth import role_required
from .db import get_db
from .utils import create_user, validate

bp = Blueprint("faculty", __name__, url_prefix="/faculty")

PROFILE_FIELDS = [
    {"name": "employee_id", "label": "Employee ID", "type": "text"},
    {"name": "name", "label": "Full name", "type": "text"},
    {"name": "email", "label": "Email", "type": "email"},
    {"name": "department", "label": "Department", "type": "text"},
]
ACCOUNT_FIELDS = [
    {"name": "username", "label": "Username", "type": "text"},
    {"name": "password", "label": "Password", "type": "password"},
]
COLUMNS = [("employee_id", "Employee ID"), ("name", "Name"),
           ("email", "Email"), ("department", "Department")]


@bp.route("/")
@role_required("admin", "faculty")  # F-010: authorized users can view
def index():
    rows = get_db().execute(
        "SELECT id, employee_id, name, email, department FROM faculty "
        "ORDER BY employee_id"
    ).fetchall()
    is_admin = g.user["role"] == "admin"
    return render_template(
        "list.html", title="Faculty", columns=COLUMNS, rows=rows,
        add_url=url_for("faculty.add") if is_admin else None,
        edit_endpoint="faculty.edit" if is_admin else None,
    )


@bp.route("/add", methods=("GET", "POST"))
@role_required("admin")
def add():
    fields = ACCOUNT_FIELDS + PROFILE_FIELDS
    if request.method == "POST":
        errors = validate(request.form, fields)
        if not errors:
            db = get_db()
            try:
                user_id = create_user(
                    db, request.form["username"].strip(),
                    request.form["password"], "faculty")
                db.execute(
                    "INSERT INTO faculty "
                    "(user_id, employee_id, name, email, department) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, request.form["employee_id"].strip(),
                     request.form["name"].strip(), request.form["email"].strip(),
                     request.form["department"].strip()))
                db.commit()
                flash("Faculty added.", "success")
                return redirect(url_for("faculty.index"))
            except IntegrityError:
                db.rollback()
                errors.append("Username or Employee ID already exists.")
        for error in errors:
            flash(error, "error")
    return render_template(
        "form.html", title="Add faculty", fields=fields, values=request.form,
        cancel_url=url_for("faculty.index"))


@bp.route("/<int:record_id>/edit", methods=("GET", "POST"))
@role_required("admin")
def edit(record_id):
    db = get_db()
    member = db.execute(
        "SELECT * FROM faculty WHERE id = ?", (record_id,)).fetchone()
    if member is None:
        abort(404)
    values = request.form if request.method == "POST" else dict(member)
    if request.method == "POST":
        errors = validate(request.form, PROFILE_FIELDS)
        if not errors:
            try:
                db.execute(
                    "UPDATE faculty SET employee_id = ?, name = ?, email = ?, "
                    "department = ? WHERE id = ?",
                    (request.form["employee_id"].strip(),
                     request.form["name"].strip(), request.form["email"].strip(),
                     request.form["department"].strip(), record_id))
                db.commit()
                flash("Faculty updated.", "success")
                return redirect(url_for("faculty.index"))
            except IntegrityError:
                db.rollback()
                errors.append("Employee ID already exists.")
        for error in errors:
            flash(error, "error")
    return render_template(
        "form.html", title="Edit faculty", fields=PROFILE_FIELDS, values=values,
        cancel_url=url_for("faculty.index"))
