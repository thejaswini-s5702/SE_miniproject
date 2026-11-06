"""Modify attendance tests (TC-Attendance-02, TC-Sec-03)."""
from src.db import get_db


def add_second_faculty(client, login):
    """Admin creates a second faculty member (id 2) with their own subject (id 2)."""
    login("admin", "admin123")
    client.post("/faculty/add", data={
        "username": "fac2", "password": "secret123", "employee_id": "F002",
        "name": "Second Faculty", "email": "f2@example.com", "department": "ECE"})
    client.post("/subjects/add", data={"code": "EC101", "name": "Circuits", "faculty_id": "2"})
    client.post("/logout")


SESSION = {"subject_id": "1", "session_date": "2026-10-20", "topic": "Intro"}


def status_of(app, student_id, session_id=1):
    with app.app_context():
        row = get_db().execute(
            "SELECT status FROM attendance WHERE class_session_id = ? AND student_id = ?",
            (session_id, student_id)).fetchone()
    return row["status"] if row else None


def recorded_session(client, login, status="present"):
    login("faculty1", "faculty123")
    client.post("/sessions/add", data=SESSION)
    client.post("/sessions/1/attendance", data={"status_1": status})


def test_faculty_modifies_attendance(app, client, login):  # TC-Attendance-02
    recorded_session(client, login, "present")
    response = client.post("/sessions/1/attendance/edit", data={"status_1": "absent"})
    assert response.status_code == 302
    assert status_of(app, 1) == "absent"


def test_edit_form_shows_saved_status(client, login):  # TC-Attendance-02
    recorded_session(client, login, "absent")
    page = client.get("/sessions/1/attendance/edit")
    assert page.status_code == 200
    assert b"checked" in page.data


def test_record_page_redirects_to_modify_when_saved(client, login):
    recorded_session(client, login)
    response = client.get("/sessions/1/attendance")
    assert response.status_code == 302
    assert "/attendance/edit" in response.headers["Location"]


def test_edit_before_recording_redirects_to_record(client, login):
    login("faculty1", "faculty123")
    client.post("/sessions/add", data=SESSION)
    response = client.get("/sessions/1/attendance/edit")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/sessions/1/attendance")


def test_student_added_later_gets_a_row(app, client, login, count):
    recorded_session(client, login)
    client.post("/logout")
    login("admin", "admin123")
    client.post("/students/add", data={
        "username": "late", "password": "secret123", "roll_no": "R2",
        "name": "Late Student", "email": "late@example.com", "semester": "3"})
    client.post("/logout")
    login("faculty1", "faculty123")
    client.post("/sessions/1/attendance/edit", data={"status_1": "present", "status_2": "absent"})
    assert count("attendance") == 2
    assert status_of(app, 2) == "absent"


def test_student_cannot_modify_own_attendance(app, client, login):  # TC-Sec-03
    recorded_session(client, login, "absent")
    client.post("/logout")
    login("student1", "student123")
    response = client.post("/sessions/1/attendance/edit", data={"status_1": "present"})
    assert response.status_code == 403
    assert status_of(app, 1) == "absent"


def test_other_faculty_cannot_modify(app, client, login):  # TC-Sec-03
    add_second_faculty(client, login)
    recorded_session(client, login, "absent")
    client.post("/logout")
    login("fac2", "secret123")
    response = client.post("/sessions/1/attendance/edit", data={"status_1": "present"})
    assert response.status_code == 404
    assert status_of(app, 1) == "absent"
