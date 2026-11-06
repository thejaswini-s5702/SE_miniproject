"""Attendance percentage tests (TC-Attendance-03)."""
from src.utils import calculate_percentage


def add_second_faculty(client, login):
    """Admin creates a second faculty member (id 2) with their own subject (id 2)."""
    login("admin", "admin123")
    client.post("/faculty/add", data={
        "username": "fac2", "password": "secret123", "employee_id": "F002",
        "name": "Second Faculty", "email": "f2@example.com", "department": "ECE"})
    client.post("/subjects/add", data={"code": "EC101", "name": "Circuits", "faculty_id": "2"})
    client.post("/logout")


SESSION = {"subject_id": "1", "session_date": "2026-10-20", "topic": "Intro"}


def test_percentage_calculation():  # TC-Attendance-03
    assert calculate_percentage(2, 3) == 66.7
    assert calculate_percentage(3, 3) == 100.0
    assert calculate_percentage(0, 4) == 0.0


def test_percentage_with_no_classes_is_zero():
    assert calculate_percentage(0, 0) == 0.0


def record_three_sessions(client, login):
    login("faculty1", "faculty123")
    for day, status in [("20", "present"), ("21", "absent"), ("22", "present")]:
        client.post("/sessions/add", data=dict(SESSION, session_date="2026-10-" + day))
    for session_id, status in [(1, "present"), (2, "absent"), (3, "present")]:
        client.post("/sessions/%d/attendance" % session_id, data={"status_1": status})


def test_summary_shows_correct_percentage(client, login):  # TC-Attendance-03
    record_three_sessions(client, login)
    page = client.get("/attendance/summary/1")
    assert page.status_code == 200
    assert b"66.7%" in page.data
    assert b"Demo Student" in page.data


def test_my_subjects_links_to_summary(client, login):
    login("faculty1", "faculty123")
    assert b"/attendance/summary/1" in client.get("/subjects/mine").data


def test_other_faculty_cannot_see_summary(client, login):
    add_second_faculty(client, login)
    login("faculty1", "faculty123")
    client.post("/logout")
    login("fac2", "secret123")
    assert client.get("/attendance/summary/1").status_code == 404


def test_student_cannot_see_summary(client, login):
    login("student1", "student123")
    assert client.get("/attendance/summary/1").status_code == 403
