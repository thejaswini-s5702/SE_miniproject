"""Class session tests (TC-Class-01)."""


def add_second_faculty(client, login):
    """Admin creates a second faculty member (id 2) with their own subject (id 2)."""
    login("admin", "admin123")
    client.post("/faculty/add", data={
        "username": "fac2", "password": "secret123", "employee_id": "F002",
        "name": "Second Faculty", "email": "f2@example.com", "department": "ECE"})
    client.post("/subjects/add", data={"code": "EC101", "name": "Circuits", "faculty_id": "2"})
    client.post("/logout")


NEW_SESSION = {"subject_id": "1", "session_date": "2026-10-20", "topic": "Intro"}


def test_faculty_creates_class_session(client, login, count):  # TC-Class-01
    login("faculty1", "faculty123")
    before = count("class_sessions")
    response = client.post("/sessions/add", data=NEW_SESSION)
    assert response.status_code == 302
    assert count("class_sessions") == before + 1
    page = client.get("/sessions/")
    assert b"CS101" in page.data
    assert b"2026-10-20" in page.data


def test_topic_is_optional(client, login, count):
    login("faculty1", "faculty123")
    data = dict(NEW_SESSION, topic="")
    assert client.post("/sessions/add", data=data).status_code == 302
    assert count("class_sessions") == 1


def test_invalid_date_is_rejected(client, login, count):  # TC-Class-01
    login("faculty1", "faculty123")
    response = client.post("/sessions/add", data=dict(NEW_SESSION, session_date="31-13-2026"))
    assert b"valid date" in response.data
    assert count("class_sessions") == 0


def test_cannot_use_another_faculty_subject(client, login, count):  # TC-Class-01
    add_second_faculty(client, login)
    login("faculty1", "faculty123")
    response = client.post("/sessions/add", data=dict(NEW_SESSION, subject_id="2"))
    assert b"Choose one of your assigned subjects" in response.data
    assert count("class_sessions") == 0


def test_faculty_edits_own_session(client, login):
    login("faculty1", "faculty123")
    client.post("/sessions/add", data=NEW_SESSION)
    response = client.post("/sessions/1/edit", data=dict(NEW_SESSION, topic="Revised topic"))
    assert response.status_code == 302
    assert b"Revised topic" in client.get("/sessions/").data


def test_other_faculty_cannot_edit_session(client, login):
    add_second_faculty(client, login)
    login("faculty1", "faculty123")
    client.post("/sessions/add", data=NEW_SESSION)
    client.post("/logout")
    login("fac2", "secret123")
    assert client.get("/sessions/1/edit").status_code == 404
    assert b"Intro" not in client.get("/sessions/").data


def test_only_faculty_can_manage_sessions(client, login):
    for username, password in [("admin", "admin123"), ("student1", "student123")]:
        login(username, password)
        assert client.get("/sessions/").status_code == 403
        assert client.get("/sessions/add").status_code == 403
        client.post("/logout")
