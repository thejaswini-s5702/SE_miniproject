"""Update faculty tests (TC-Faculty-02)."""

UPDATE = {
    "employee_id": "F001", "name": "Updated Faculty",
    "email": "faculty1@example.com", "department": "ISE",
}


def test_admin_updates_faculty(client, login):
    login("admin", "admin123")
    assert client.post("/faculty/1/edit", data=UPDATE).status_code == 302
    page = client.get("/faculty/")
    assert b"Updated Faculty" in page.data
    assert b"ISE" in page.data


def test_edit_unknown_faculty_returns_404(client, login):
    login("admin", "admin123")
    assert client.get("/faculty/999/edit").status_code == 404


def test_non_admin_cannot_edit_faculty(client, login):
    login("faculty1", "faculty123")
    assert client.post("/faculty/1/edit", data=UPDATE).status_code == 403
