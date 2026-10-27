"""Data layer: SQLite connection, schema setup and demo data."""
import sqlite3

import click
from flask import current_app, g

from .utils import create_user


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    with current_app.open_resource("schema.sql") as schema:
        db.executescript(schema.read().decode("utf8"))


def create_admin(username="admin", password="admin123"):
    db = get_db()
    exists = db.execute(
        "SELECT 1 FROM users WHERE username = ?", (username,)
    ).fetchone()
    if exists is None:
        create_user(db, username, password, "admin")
        db.commit()


def seed_demo():
    """Add one faculty, one student and one subject for demos and tests."""
    db = get_db()
    if db.execute("SELECT 1 FROM users WHERE username = 'faculty1'").fetchone():
        return
    faculty_user = create_user(db, "faculty1", "faculty123", "faculty")
    cursor = db.execute(
        "INSERT INTO faculty (user_id, employee_id, name, email, department) "
        "VALUES (?, ?, ?, ?, ?)",
        (faculty_user, "F001", "Dr. Demo Faculty", "faculty1@example.com", "CSE"),
    )
    faculty_id = cursor.lastrowid
    student_user = create_user(db, "student1", "student123", "student")
    db.execute(
        "INSERT INTO students (user_id, roll_no, name, email, semester) "
        "VALUES (?, ?, ?, ?, ?)",
        (student_user, "PES2UG24CS001", "Demo Student", "student1@example.com", 3),
    )
    db.execute(
        "INSERT INTO subjects (code, name, faculty_id) VALUES (?, ?, ?)",
        ("CS101", "Software Engineering", faculty_id),
    )
    db.commit()


@click.command("init-db")
def init_db_command():
    """Create tables and the default admin account."""
    init_db()
    create_admin()
    click.echo("Database ready. Admin login: admin / admin123 (change it!)")


@click.command("seed-demo")
def seed_demo_command():
    """Add demo faculty, student and subject."""
    seed_demo()
    click.echo("Demo data added: faculty1/faculty123, student1/student123")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_demo_command)
