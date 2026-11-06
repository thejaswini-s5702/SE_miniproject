"""Student attendance view tests (TC-Attendance-04, TC-Sec-05)."""

SESSION = {"subject_id": "1", "session_date": "2026-10-20", "topic": "Intro"}


def second_student(client, login):
    login("admin", "admin123")
    client.post("/students/add", data={
        "username": "stud2", "password": "secret123", "roll_no": "R2",
        "name": "Second Student", "email": "s2@example.com", "semester": "3"})
    client.post("/logout")


def record_two_sessions(client, login):
    login("faculty1", "faculty123")
    for day in ("20", "21"):
        client.post("/sessions/add", data=dict(SESSION, session_date="2026-10-" + day))
    client.post("/sessions/1/attendance", data={"status_1": "present", "status_2": "absent"})
    client.post("/sessions/2/attendance", data={"status_1": "absent", "status_2": "absent"})
    client.post("/logout")


def test_student_sees_status_history_and_percentage(client, login):  # TC-Attendance-04
    second_student(client, login)
    record_two_sessions(client, login)
    login("student1", "student123")
    page = client.get("/my-attendance")
    assert page.status_code == 200
    assert b"50.0%" in page.data
    assert b"CS101" in page.data
    assert b"2026-10-20" in page.data
    assert b"Present" in page.data and b"Absent" in page.data


def test_student_sees_only_own_records(client, login):  # TC-Sec-05
    second_student(client, login)
    record_two_sessions(client, login)
    login("stud2", "secret123")
    page = client.get("/my-attendance")
    assert b"Second Student" in page.data
    assert b"0.0%" in page.data
    assert b"Demo Student" not in page.data


def test_empty_state_before_any_attendance(client, login):
    login("student1", "student123")
    assert b"No attendance recorded yet" in client.get("/my-attendance").data


def test_only_students_can_open_my_attendance(client, login):  # TC-Sec-05
    login("faculty1", "faculty123")
    assert client.get("/my-attendance").status_code == 403


def test_my_attendance_requires_login(client):  # TC-Sec-05
    assert client.get("/my-attendance").status_code == 302
