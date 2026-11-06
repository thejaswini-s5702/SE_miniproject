"""Attendance component (SAMS-F-014 to F-017)."""
from sqlite3 import IntegrityError

from flask import (Blueprint, abort, flash, g, redirect, render_template,
                   request, url_for)

from .auth import role_required
from .class_sessions import get_own_session
from .db import get_db
from .utils import calculate_percentage

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


@bp.route("/attendance/summary/<int:record_id>")
@role_required("faculty")
def summary(record_id):
    """Attendance percentage of every student for one of the faculty's subjects."""
    db = get_db()
    subject = db.execute(
        "SELECT s.id, s.code, s.name FROM subjects s "
        "JOIN faculty f ON f.id = s.faculty_id "
        "WHERE s.id = ? AND f.user_id = ?", (record_id, g.user["id"])
    ).fetchone()
    if subject is None:
        abort(404)
    records = db.execute(
        "SELECT st.id, st.roll_no, st.name, COUNT(a.id) AS total, "
        "COALESCE(SUM(a.status = 'present'), 0) AS present "
        "FROM students st "
        "LEFT JOIN (SELECT a2.* FROM attendance a2 "
        "           JOIN class_sessions cs ON cs.id = a2.class_session_id "
        "           WHERE cs.subject_id = ?) a ON a.student_id = st.id "
        "GROUP BY st.id ORDER BY st.roll_no", (record_id,)
    ).fetchall()
    rows = [{
        "id": r["id"], "roll_no": r["roll_no"], "name": r["name"],
        "present": r["present"], "total": r["total"],
        "percentage": f"{calculate_percentage(r['present'], r['total'])}%",
    } for r in records]
    return render_template(
        "list.html", title=f"Attendance summary: {subject['code']}",
        columns=[("roll_no", "SRN"), ("name", "Name"), ("present", "Present"),
                 ("total", "Classes"), ("percentage", "Attendance %")],
        rows=rows)


@bp.route("/my-attendance")
@role_required("student")  # F-017 / SR-005: a student only ever sees their own records
def mine():
    db = get_db()
    student = db.execute(
        "SELECT id, roll_no, name FROM students WHERE user_id = ?", (g.user["id"],)
    ).fetchone()
    if student is None:
        abort(404)
    per_subject = db.execute(
        "SELECT s.code, s.name, COUNT(a.id) AS total, "
        "COALESCE(SUM(a.status = 'present'), 0) AS present "
        "FROM attendance a "
        "JOIN class_sessions cs ON cs.id = a.class_session_id "
        "JOIN subjects s ON s.id = cs.subject_id "
        "WHERE a.student_id = ? GROUP BY s.id ORDER BY s.code", (student["id"],)
    ).fetchall()
    subjects = [{
        "code": r["code"], "name": r["name"], "present": r["present"],
        "total": r["total"],
        "percentage": calculate_percentage(r["present"], r["total"]),
    } for r in per_subject]
    present = sum(r["present"] for r in per_subject)
    total = sum(r["total"] for r in per_subject)
    history = db.execute(
        "SELECT cs.session_date, s.code, cs.topic, a.status FROM attendance a "
        "JOIN class_sessions cs ON cs.id = a.class_session_id "
        "JOIN subjects s ON s.id = cs.subject_id "
        "WHERE a.student_id = ? ORDER BY cs.session_date DESC, cs.id DESC",
        (student["id"],)
    ).fetchall()
    return render_template(
        "attendance_student.html", student=student, subjects=subjects,
        history=history, overall=calculate_percentage(present, total), total=total)
