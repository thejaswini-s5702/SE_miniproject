"""Add and view faculty tests (TC-Faculty-01, TC-Faculty-03)."""

NEW_FACULTY = {
    "username": "newfac", "password": "secret123", "employee_id": "F900",
    "name": "New Faculty", "email": "fac@example.com", "department": "ECE",
}


def test_admin_adds_faculty(client, login, count):  # TC-Faculty-01
    login("admin", "admin123")
    before = count("faculty")
    assert client.post("/faculty/add", data=NEW_FACULTY).status_code == 302
    assert count("faculty") == before + 1
    assert b"New Faculty" in client.get("/faculty/").data


def test_duplicate_employee_id_is_rejected(client, login, count):  # TC-Faculty-01
    login("admin", "admin123")
    client.post("/faculty/add", data=NEW_FACULTY)
    before = count("faculty")
    response = client.post("/faculty/add", data=dict(NEW_FACULTY, username="other"))
    assert b"already exists" in response.data
    assert count("faculty") == before


def test_faculty_can_view_faculty_list(client, login):  # TC-Faculty-03
    login("faculty1", "faculty123")
    response = client.get("/faculty/")
    assert response.status_code == 200
    assert b"Dr. Demo Faculty" in response.data


def test_student_cannot_view_faculty_list(client, login):  # TC-Faculty-03
    login("student1", "student123")
    assert client.get("/faculty/").status_code == 403


def test_non_admin_cannot_add_faculty(client, login, count):
    login("faculty1", "faculty123")
    before = count("faculty")
    assert client.post("/faculty/add", data=NEW_FACULTY).status_code == 403
    assert count("faculty") == before
