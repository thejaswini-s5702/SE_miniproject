import pytest

from src import create_app
from src.db import create_admin, get_db, init_db, seed_demo


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite")})
    with app.app_context():
        init_db()
        create_admin()
        seed_demo()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def login(client):
    def do_login(username, password):
        return client.post("/login", data={"username": username, "password": password})
    return do_login


@pytest.fixture
def count(app):
    def do_count(table):
        with app.app_context():
            return get_db().execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return do_count
