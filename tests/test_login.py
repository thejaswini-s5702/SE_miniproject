"""Login tests (TC-Auth-01, TC-Auth-03, TC-Sec-01, TC-Sec-04)."""


def test_valid_login_reaches_dashboard(client, login):  # TC-Auth-01
    response = login("admin", "admin123")
    assert response.status_code == 302
    page = client.get("/dashboard")
    assert page.status_code == 200
    assert b"admin (admin)" in page.data


def test_invalid_login_is_rejected(client, login):  # TC-Auth-03
    response = login("admin", "wrong-password")
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data
    assert client.get("/dashboard").status_code == 302  # no session created


def test_unknown_user_gets_same_message(login):  # TC-Auth-03
    response = login("nobody", "whatever")
    assert response.status_code == 401
    assert b"Invalid username or password" in response.data


def test_login_required_for_dashboard(client):  # TC-Sec-01
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_passwords_are_not_stored_in_plain_text(app):  # TC-Sec-04
    from src.db import get_db
    with app.app_context():
        hashes = [r[0] for r in get_db().execute("SELECT password_hash FROM users")]
    assert hashes
    for stored in hashes:
        assert stored not in ("admin123", "faculty123", "student123")
        assert ":" in stored or stored.startswith(("scrypt", "pbkdf2"))


def test_logout_ends_session(client, login):
    login("admin", "admin123")
    client.post("/logout")
    assert client.get("/dashboard").status_code == 302
