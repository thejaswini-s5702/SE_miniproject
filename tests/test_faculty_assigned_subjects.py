
"""Tests for faculty assigned subjects (SAMS-F-011)."""


def test_faculty_sees_assigned_subjects(client, login):
    login("admin", "admin123")
    client.post("/subjects/add", data={
        "code": "CS201",
        "name": "Assigned Database",
        "faculty_id": "1",
    })
    client.post("/logout")

    login("faculty1", "faculty123")
    response = client.get("/subjects/assigned")

    assert response.status_code == 200
    assert b"Assigned Database" in response.data
    assert b"CS201" in response.data


def test_faculty_sees_only_own_subjects(client, login):
    login("admin", "admin123")
    client.post("/subjects/add", data={
        "code": "CS201",
        "name": "Faculty One Subject",
        "faculty_id": "1",
    })
    client.post("/subjects/add", data={
        "code": "CS202",
        "name": "Unassigned Subject",
        "faculty_id": "",
    })
    client.post("/logout")

    login("faculty1", "faculty123")
    response = client.get("/subjects/assigned")

    assert response.status_code == 200
    assert b"Faculty One Subject" in response.data
    assert b"Unassigned Subject" not in response.data


def test_admin_and_student_cannot_access_assigned_subjects(client, login):
    for username, password in [
        ("admin", "admin123"),
        ("student1", "student123"),
    ]:
        login(username, password)
        response = client.get("/subjects/assigned")
        assert response.status_code == 403
        client.post("/logout")
