"""Update student tests (TC-Student-02)."""

UPDATE = {
    "roll_no": "PES2UG24CS001", "name": "Renamed Student",
    "email": "student1@example.com", "semester": "5",
}


def test_admin_updates_student(client, login):
    login("admin", "admin123")
    response = client.post("/students/1/edit", data=UPDATE)
    assert response.status_code == 302
    assert b"Renamed Student" in client.get("/students/").data


def test_edit_form_shows_current_values(client, login):
    login("admin", "admin123")
    page = client.get("/students/1/edit")
    assert page.status_code == 200
    assert b"Demo Student" in page.data


def test_edit_unknown_student_returns_404(client, login):
    login("admin", "admin123")
    assert client.get("/students/999/edit").status_code == 404


def test_edit_rejects_invalid_semester(client, login):
    login("admin", "admin123")
    response = client.post("/students/1/edit", data=dict(UPDATE, semester="abc"))
    assert b"must be a number" in response.data
