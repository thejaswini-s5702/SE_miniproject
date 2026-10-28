"""Add student tests (TC-Student-01)."""

NEW_STUDENT = {
    "username": "newstudent", "password": "secret123", "roll_no": "PES2UG24CS999",
    "name": "New Student", "email": "new@example.com", "semester": "2",
}


def test_admin_adds_student(client, login, count):
    login("admin", "admin123")
    before = count("students")
    response = client.post("/students/add", data=NEW_STUDENT)
    assert response.status_code == 302
    assert count("students") == before + 1
    assert b"PES2UG24CS999" in client.get("/students/").data


def test_new_student_can_log_in(client, login):
    login("admin", "admin123")
    client.post("/students/add", data=NEW_STUDENT)
    client.post("/logout")
    assert login("newstudent", "secret123").status_code == 302


def test_duplicate_student_is_rejected(client, login, count):
    login("admin", "admin123")
    client.post("/students/add", data=NEW_STUDENT)
    before = count("students")
    response = client.post("/students/add", data=dict(NEW_STUDENT, username="other"))
    assert response.status_code == 200
    assert b"already exists" in response.data
    assert count("students") == before


def test_missing_fields_are_rejected(client, login, count):
    login("admin", "admin123")
    before = count("students")
    response = client.post("/students/add", data={"username": "x"})
    assert b"is required" in response.data
    assert count("students") == before


def test_student_list_requires_login(client):
    assert client.get("/students/").status_code == 302


def test_student_role_cannot_open_student_pages(client, login):
    login("student1", "student123")
    assert client.get("/students/").status_code == 403
    assert client.get("/students/add").status_code == 403
