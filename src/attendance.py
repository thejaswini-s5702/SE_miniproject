"""Attendance component (SAMS-F-014, F-015)."""
from sqlite3 import IntegrityError

from flask import Blueprint, flash, redirect, render_template, request, url_for

from .auth import role_required
from .class_sessions import get_own_session
from .db import get_db

bp = Blueprint("attendance", __name__)


def all_students():
    return get_db().execute(
        "SELECT id, roll_no, name FROM students ORDER BY roll_no").fetchall()


def parse_statuses(form, students):
    """Return {student_id: status}, or None if any choice is missing or invalid."""
    statuses = {}
    for student in students:
        value = form.get(f"status_{student['id']}")
        if value not in ("present", "absent"):
            return None
        statuses[student["id"]] = value
    return statuses


@bp.route("/sessions/<int:record_id>/attendance", methods=("GET", "POST"))
@role_required("faculty")  # SR-003: students can never reach this page
def record(record_id):
    class_session = get_own_session(record_id)
    db = get_db()
    already = db.execute(
        "SELECT 1 FROM attendance WHERE class_session_id = ?", (record_id,)
    ).fetchone()
    if already:
        return redirect(url_for("attendance.edit", record_id=record_id))
    students = all_students()
    if not students:
        flash("Add students before recording attendance.", "error")
        return redirect(url_for("class_sessions.index"))
    if request.method == "POST":
        statuses = parse_statuses(request.form, students)
        if statuses is None:
            flash("Choose present or absent for every student.", "error")
        else:
            try:
                db.executemany(
                    "INSERT INTO attendance (class_session_id, student_id, status) "
                    "VALUES (?, ?, ?)",
                    [(record_id, sid, status) for sid, status in statuses.items()])
                db.commit()  # all students saved together, or none
            except IntegrityError:
                db.rollback()
                flash("Could not save attendance.", "error")
            else:
                flash("Attendance recorded.", "success")
                return redirect(url_for("class_sessions.index"))
    return render_template(
        "attendance_form.html", title="Record attendance",
        class_session=class_session, students=students, current={},
        cancel_url=url_for("class_sessions.index"))


@bp.route("/sessions/<int:record_id>/attendance/edit", methods=("GET", "POST"))
@role_required("faculty")  # F-015 / SR-003: only the owning faculty member may modify
def edit(record_id):
    class_session = get_own_session(record_id)
    db = get_db()
    current = {row["student_id"]: row["status"] for row in db.execute(
        "SELECT student_id, status FROM attendance WHERE class_session_id = ?",
        (record_id,))}
    if not current:
        return redirect(url_for("attendance.record", record_id=record_id))
    students = all_students()
    if request.method == "POST":
        statuses = parse_statuses(request.form, students)
        if statuses is None:
            flash("Choose present or absent for every student.", "error")
        else:
            db.executemany(
                "INSERT INTO attendance (class_session_id, student_id, status) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT (class_session_id, student_id) "
                "DO UPDATE SET status = excluded.status",
                [(record_id, sid, status) for sid, status in statuses.items()])
            db.commit()
            flash("Attendance updated.", "success")
            return redirect(url_for("class_sessions.index"))
    return render_template(
        "attendance_form.html", title="Modify attendance",
        class_session=class_session, students=students, current=current,
        cancel_url=url_for("class_sessions.index"))
