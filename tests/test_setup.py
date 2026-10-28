"""Project setup tests: database schema and app factory (SETUP-01)."""
from src.db import get_db, seed_demo


def test_database_tables_created(app):
    with app.app_context():
        rows = get_db().execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        tables = {row[0] for row in rows}
    expected = {"users", "students", "faculty", "subjects", "class_sessions", "attendance"}
    assert expected <= tables


def test_seed_demo_is_idempotent(app, count):
    before = count("users")
    with app.app_context():
        seed_demo()
    assert count("users") == before


def test_unknown_page_returns_404(client):
    assert client.get("/nothing-here").status_code == 404
