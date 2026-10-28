"""Shared helpers (validation and account creation)."""
from werkzeug.security import generate_password_hash

MIN_PASSWORD_LENGTH = 6


def validate(values, fields):
    """Return a list of error messages for a submitted form."""
    errors = []
    for field in fields:
        if field["type"] == "select":
            continue
        value = values.get(field["name"], "").strip()
        if not value:
            errors.append(f"{field['label']} is required.")
        elif field["type"] == "number" and not value.isdigit():
            errors.append(f"{field['label']} must be a number.")
        elif field["type"] == "password" and len(value) < MIN_PASSWORD_LENGTH:
            errors.append(
                f"{field['label']} must be at least {MIN_PASSWORD_LENGTH} characters."
            )
    return errors


def create_user(db, username, password, role):
    """Insert a login account (password stored hashed, SAMS-SR-004).

    The caller is responsible for committing the transaction.
    """
    cursor = db.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, generate_password_hash(password), role),
    )
    return cursor.lastrowid
