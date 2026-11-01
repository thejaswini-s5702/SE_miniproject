"""Record attendance tests (TC-Attendance-01)."""


def add_second_faculty(client, login):
    """Admin creates a second faculty member (id 2) with their own subject (id 2)."""
    login("admin", "admin123")
    client.post("/faculty/add", data={
        "username": "fac2", "password": "secret123", "employee_id": "F002",
        "name": "Second Faculty", "email": "f2@example.com", "department": "ECE"})
    client.post("/subjects/add", data={"code": "EC101", "name": "Circuits", "faculty_id": "2"})
    client.post("/logout")


SESSION = {"subject_id": "1", "session_date": "2026-10-20", "topic": "Intro"}


def make_session(client, login):
    login("faculty1", "faculty123")
    client.post("/sessions/add", data=SESSION)


def test_record_form_lists_students(client, login):  # TC-Attendance-01
    make_session(client, login)
    page = client.get("/sessions/1/attendance")
    assert page.status_code == 200
    assert b"Demo Student" in page.data


def test_faculty_records_attendance(client, login, count):  # TC-Attendance-01
    make_session(client, login)
    response = client.post("/sessions/1/attendance", data={"status_1": "present"})
    assert response.status_code == 302
    assert count("attendance") == 1


def test_missing_choice_saves_nothing(client, login, count):  # NFR-005
    make_session(client, login)
    response = client.post("/sessions/1/attendance", data={})
    assert b"Choose present or absent" in response.data
    assert count("attendance") == 0


def test_cannot_record_twice(client, login, count):
    make_session(client, login)
    client.post("/sessions/1/attendance", data={"status_1": "present"})
    client.post("/sessions/1/attendance", data={"status_1": "absent"})
    assert count("attendance") == 1


def test_other_faculty_cannot_record(client, login, count):
    add_second_faculty(client, login)
    make_session(client, login)
    client.post("/logout")
    login("fac2", "secret123")
    assert client.get("/sessions/1/attendance").status_code == 404
    assert client.post("/sessions/1/attendance", data={"status_1": "present"}).status_code == 404
    assert count("attendance") == 0


def test_students_cannot_record_attendance(client, login, count):  # TC-Sec-03
    make_session(client, login)
    client.post("/logout")
    login("student1", "student123")
    assert client.get("/sessions/1/attendance").status_code == 403
    assert client.post("/sessions/1/attendance", data={"status_1": "present"}).status_code == 403
    assert count("attendance") == 0
