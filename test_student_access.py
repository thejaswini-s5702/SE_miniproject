"""View and access-control tests (TC-Student-03, TC-Student-04)."""


def test_faculty_can_view_students(client, login):  # TC-Student-03
    login("faculty1", "faculty123")
    response = client.get("/students/")
    assert response.status_code == 200
    assert b"Demo Student" in response.data
    assert b"+ Add" not in response.data  # view-only for faculty


def test_admin_sees_add_button(client, login):
    login("admin", "admin123")
    assert b"+ Add" in client.get("/students/").data


def test_student_cannot_view_student_list(client, login):  # TC-Student-03
    login("student1", "student123")
    assert client.get("/students/").status_code == 403


def test_unauthorized_users_cannot_modify_students(client, login, count):  # TC-Student-04
    before = count("students")
    new = {"username": "x1", "password": "secret123", "roll_no": "R1",
           "name": "X", "email": "x@example.com", "semester": "1"}
    for username, password in [("student1", "student123"), ("faculty1", "faculty123")]:
        login(username, password)
        assert client.post("/students/add", data=new).status_code == 403
        assert client.post("/students/1/edit", data={}).status_code == 403
        client.post("/logout")
    assert count("students") == before
