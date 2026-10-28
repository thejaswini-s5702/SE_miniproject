"""Subject management tests (TC-Subject-01)."""


def test_admin_adds_subject_with_faculty(client, login, count):
    login("admin", "admin123")
    before = count("subjects")
    response = client.post("/subjects/add", data={
        "code": "CS202", "name": "Databases", "faculty_id": "1"})
    assert response.status_code == 302
    assert count("subjects") == before + 1
    page = client.get("/subjects/")
    assert b"Databases" in page.data
    assert b"Dr. Demo Faculty" in page.data


def test_duplicate_subject_code_is_rejected(client, login, count):
    login("admin", "admin123")
    before = count("subjects")
    response = client.post("/subjects/add", data={
        "code": "CS101", "name": "Duplicate", "faculty_id": ""})
    assert b"already exists" in response.data
    assert count("subjects") == before


def test_admin_edits_subject_and_unassigns_faculty(client, login):
    login("admin", "admin123")
    response = client.post("/subjects/1/edit", data={
        "code": "CS101", "name": "Software Engineering II", "faculty_id": ""})
    assert response.status_code == 302
    assert b"Software Engineering II" in client.get("/subjects/").data


def test_non_admin_cannot_manage_subjects(client, login):
    for username, password in [("faculty1", "faculty123"), ("student1", "student123")]:
        login(username, password)
        assert client.get("/subjects/").status_code == 403
        assert client.get("/subjects/add").status_code == 403
        client.post("/logout")
