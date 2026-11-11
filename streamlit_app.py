"""Streamlit interface for the Student Attendance Management System."""
from contextlib import contextmanager
from datetime import date, datetime
import os
from pathlib import Path
import sqlite3

import streamlit as st
from werkzeug.security import check_password_hash

from src.utils import create_user


ROOT = Path(__file__).resolve().parent
DATABASE_PATH = Path(
    os.environ.get("SAMS_DATABASE", ROOT / "instance" / "sams.sqlite")
)


@contextmanager
def database():
    """Open a short-lived SQLite connection with foreign keys enabled."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    """Create the schema and default admin when starting a new database."""
    schema_path = ROOT / "src" / "schema.sql"
    with database() as db:
        db.executescript(schema_path.read_text(encoding="utf-8"))
        exists = db.execute(
            "SELECT 1 FROM users WHERE username = ?", ("admin",)
        ).fetchone()
        if exists is None:
            create_user(db, "admin", "admin123", "admin")


def query_all(sql, parameters=()):
    with database() as db:
        return [dict(row) for row in db.execute(sql, parameters).fetchall()]


def query_one(sql, parameters=()):
    with database() as db:
        row = db.execute(sql, parameters).fetchone()
        return dict(row) if row is not None else None


def authenticate(username, password):
    user = query_one(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        (username.strip(),),
    )
    if user is None or not check_password_hash(user["password_hash"], password):
        return None
    return {key: user[key] for key in ("id", "username", "role")}


def save_student(values, student_id=None):
    with database() as db:
        if student_id is None:
            user_id = create_user(
                db, values["username"].strip(), values["password"], "student"
            )
            db.execute(
                "INSERT INTO students (user_id, roll_no, name, email, semester) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    values["roll_no"].strip(),
                    values["name"].strip(),
                    values["email"].strip(),
                    int(values["semester"]),
                ),
            )
        else:
            db.execute(
                "UPDATE students SET roll_no = ?, name = ?, email = ?, semester = ? "
                "WHERE id = ?",
                (
                    values["roll_no"].strip(),
                    values["name"].strip(),
                    values["email"].strip(),
                    int(values["semester"]),
                    student_id,
                ),
            )


def save_faculty(values, faculty_id=None):
    with database() as db:
        if faculty_id is None:
            user_id = create_user(
                db, values["username"].strip(), values["password"], "faculty"
            )
            db.execute(
                "INSERT INTO faculty "
                "(user_id, employee_id, name, email, department) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    values["employee_id"].strip(),
                    values["name"].strip(),
                    values["email"].strip(),
                    values["department"].strip(),
                ),
            )
        else:
            db.execute(
                "UPDATE faculty SET employee_id = ?, name = ?, email = ?, "
                "department = ? WHERE id = ?",
                (
                    values["employee_id"].strip(),
                    values["name"].strip(),
                    values["email"].strip(),
                    values["department"].strip(),
                    faculty_id,
                ),
            )


def save_subject(values, subject_id=None):
    faculty_id = values["faculty_id"]
    with database() as db:
        if subject_id is None:
            db.execute(
                "INSERT INTO subjects (code, name, faculty_id) VALUES (?, ?, ?)",
                (values["code"].strip(), values["name"].strip(), faculty_id),
            )
        else:
            db.execute(
                "UPDATE subjects SET code = ?, name = ?, faculty_id = ? WHERE id = ?",
                (values["code"].strip(), values["name"].strip(), faculty_id, subject_id),
            )


def save_class_session(values, faculty_user_id, session_id=None):
    owned_subject = query_one(
        "SELECT s.id FROM subjects s JOIN faculty f ON f.id = s.faculty_id "
        "WHERE s.id = ? AND f.user_id = ?",
        (values["subject_id"], faculty_user_id),
    )
    if owned_subject is None:
        raise ValueError("Choose one of your assigned subjects.")

    with database() as db:
        if session_id is None:
            db.execute(
                "INSERT INTO class_sessions (subject_id, session_date, topic) "
                "VALUES (?, ?, ?)",
                (values["subject_id"], values["session_date"], values["topic"] or None),
            )
        else:
            db.execute(
                "UPDATE class_sessions SET subject_id = ?, session_date = ?, topic = ? "
                "WHERE id = ?",
                (
                    values["subject_id"],
                    values["session_date"],
                    values["topic"] or None,
                    session_id,
                ),
            )


def attendance_percentage(present, total):
    return round(present * 100 / total, 1) if total else 0.0


def show_table(rows, empty_message="No records yet."):
    if rows:
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.info(empty_message)


def render_login():
    st.title("Student Attendance Management System")
    st.caption("Sign in to manage classes and attendance.")
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Attendance, kept simple")
        st.write(
            "Faculty can manage class sessions and record attendance. "
            "Students can check their own attendance. Administrators manage "
            "the people and subjects in the system."
        )
    with right:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log in", type="primary", width="stretch")
        if submitted:
            user = authenticate(username, password)
            if user is None:
                st.error("Invalid username or password.")
            else:
                st.session_state["user"] = user
                st.rerun()


def render_dashboard(user):
    st.title(f"Welcome, {user['username']}")
    st.caption(f"{user['role'].capitalize()} dashboard")

    if user["role"] == "admin":
        counts = {
            "Students": query_one("SELECT COUNT(*) AS count FROM students")["count"],
            "Faculty": query_one("SELECT COUNT(*) AS count FROM faculty")["count"],
            "Subjects": query_one("SELECT COUNT(*) AS count FROM subjects")["count"],
        }
    elif user["role"] == "faculty":
        counts = {
            "My subjects": query_one(
                "SELECT COUNT(*) AS count FROM subjects s "
                "JOIN faculty f ON f.id = s.faculty_id WHERE f.user_id = ?",
                (user["id"],),
            )["count"],
            "My class sessions": query_one(
                "SELECT COUNT(*) AS count FROM class_sessions cs "
                "JOIN subjects s ON s.id = cs.subject_id "
                "JOIN faculty f ON f.id = s.faculty_id WHERE f.user_id = ?",
                (user["id"],),
            )["count"],
            "Students": query_one("SELECT COUNT(*) AS count FROM students")["count"],
        }
    else:
        student = query_one(
            "SELECT id FROM students WHERE user_id = ?", (user["id"],)
        )
        count = 0
        percentage = 0.0
        if student:
            summary = query_one(
                "SELECT COUNT(*) AS total, "
                "COALESCE(SUM(status = 'present'), 0) AS present "
                "FROM attendance WHERE student_id = ?",
                (student["id"],),
            )
            count = summary["total"]
            percentage = attendance_percentage(summary["present"], count)
        counts = {"Classes recorded": count, "Overall attendance": f"{percentage}%"}

    columns = st.columns(len(counts))
    for column, (label, value) in zip(columns, counts.items()):
        column.metric(label, value)
    st.divider()
    if user["role"] == "admin":
        st.write("Use the sidebar to manage students, faculty, and subjects.")
    elif user["role"] == "faculty":
        st.write("Use the sidebar to manage class sessions and record attendance.")
    else:
        st.write("Your attendance records are available under My attendance.")


def render_students(role):
    st.title("Students")
    rows = query_all(
        "SELECT id, roll_no AS SRN, name AS Name, email AS Email, "
        "semester AS Semester FROM students ORDER BY roll_no"
    )
    if role == "admin":
        with st.expander("Add student"):
            with st.form("add_student"):
                username = st.text_input("Username", key="student_username")
                password = st.text_input(
                    "Password (at least 6 characters)",
                    type="password",
                    key="student_password",
                )
                roll_no = st.text_input("SRN", key="student_roll")
                name = st.text_input("Full name", key="student_name")
                email = st.text_input("Email", key="student_email")
                semester = st.number_input(
                    "Semester", min_value=1, max_value=12, step=1, key="student_semester"
                )
                submitted = st.form_submit_button("Add student", type="primary")
            if submitted:
                if not all((username.strip(), roll_no.strip(), name.strip(), email.strip())):
                    st.error("Complete all fields.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        save_student(
                            {
                                "username": username,
                                "password": password,
                                "roll_no": roll_no,
                                "name": name,
                                "email": email,
                                "semester": semester,
                            }
                        )
                        st.success("Student added.")
                    except sqlite3.IntegrityError:
                        st.error("Username or SRN already exists.")

    show_table([{k: v for k, v in row.items() if k != "id"} for row in rows])

    if role == "admin" and rows:
        with st.expander("Edit student"):
            selected = st.selectbox(
                "Select student",
                rows,
                format_func=lambda row: f"{row['SRN']} - {row['Name']}",
                key="edit_student_select",
            )
            with st.form("edit_student"):
                roll_no = st.text_input("SRN", value=selected["SRN"])
                name = st.text_input("Full name", value=selected["Name"])
                email = st.text_input("Email", value=selected["Email"])
                semester = st.number_input(
                    "Semester",
                    min_value=1,
                    max_value=12,
                    value=int(selected["Semester"]),
                    step=1,
                )
                submitted = st.form_submit_button("Save changes")
            if submitted:
                if not all((roll_no.strip(), name.strip(), email.strip())):
                    st.error("Complete all fields.")
                else:
                    try:
                        save_student(
                            {
                                "roll_no": roll_no,
                                "name": name,
                                "email": email,
                                "semester": semester,
                            },
                            selected["id"],
                        )
                        st.success("Student updated.")
                    except sqlite3.IntegrityError:
                        st.error("SRN already exists.")


def render_faculty(role):
    st.title("Faculty")
    rows = query_all(
        "SELECT id, employee_id AS 'Employee ID', name AS Name, "
        "email AS Email, department AS Department FROM faculty ORDER BY employee_id"
    )
    if role == "admin":
        with st.expander("Add faculty"):
            with st.form("add_faculty"):
                username = st.text_input("Username", key="faculty_username")
                password = st.text_input(
                    "Password (at least 6 characters)",
                    type="password",
                    key="faculty_password",
                )
                employee_id = st.text_input("Employee ID", key="faculty_employee_id")
                name = st.text_input("Full name", key="faculty_name")
                email = st.text_input("Email", key="faculty_email")
                department = st.text_input("Department", key="faculty_department")
                submitted = st.form_submit_button("Add faculty", type="primary")
            if submitted:
                values = (username.strip(), employee_id.strip(), name.strip(),
                          email.strip(), department.strip())
                if not all(values):
                    st.error("Complete all fields.")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        save_faculty(
                            {
                                "username": username,
                                "password": password,
                                "employee_id": employee_id,
                                "name": name,
                                "email": email,
                                "department": department,
                            }
                        )
                        st.success("Faculty added.")
                    except sqlite3.IntegrityError:
                        st.error("Username or Employee ID already exists.")

    show_table([{k: v for k, v in row.items() if k != "id"} for row in rows])

    if role == "admin" and rows:
        with st.expander("Edit faculty"):
            selected = st.selectbox(
                "Select faculty",
                rows,
                format_func=lambda row: f"{row['Employee ID']} - {row['Name']}",
                key="edit_faculty_select",
            )
            with st.form("edit_faculty"):
                employee_id = st.text_input("Employee ID", value=selected["Employee ID"])
                name = st.text_input("Full name", value=selected["Name"])
                email = st.text_input("Email", value=selected["Email"])
                department = st.text_input("Department", value=selected["Department"])
                submitted = st.form_submit_button("Save changes")
            if submitted:
                if not all((employee_id.strip(), name.strip(), email.strip(),
                            department.strip())):
                    st.error("Complete all fields.")
                else:
                    try:
                        save_faculty(
                            {
                                "employee_id": employee_id,
                                "name": name,
                                "email": email,
                                "department": department,
                            },
                            selected["id"],
                        )
                        st.success("Faculty updated.")
                    except sqlite3.IntegrityError:
                        st.error("Employee ID already exists.")


def render_subjects():
    st.title("Subjects")
    faculty = query_all(
        "SELECT id, name, employee_id FROM faculty ORDER BY name"
    )
    faculty_options = {None: "Unassigned"}
    faculty_options.update({
        member["id"]: f"{member['name']} ({member['employee_id']})"
        for member in faculty
    })
    rows = query_all(
        "SELECT s.id, s.code AS Code, s.name AS Subject, s.faculty_id, "
        "COALESCE(f.name, 'Unassigned') AS 'Assigned faculty' "
        "FROM subjects s LEFT JOIN faculty f ON f.id = s.faculty_id "
        "ORDER BY s.code"
    )

    with st.expander("Add subject"):
        with st.form("add_subject"):
            code = st.text_input("Subject code", key="subject_code")
            name = st.text_input("Subject name", key="subject_name")
            faculty_id = st.selectbox(
                "Assigned faculty",
                list(faculty_options),
                format_func=lambda value: faculty_options[value],
                key="subject_faculty",
            )
            submitted = st.form_submit_button("Add subject", type="primary")
        if submitted:
            if not code.strip() or not name.strip():
                st.error("Enter a subject code and name.")
            else:
                try:
                    save_subject(
                        {"code": code, "name": name, "faculty_id": faculty_id}
                    )
                    st.success("Subject added.")
                except sqlite3.IntegrityError:
                    st.error("Subject code already exists or faculty is invalid.")

    show_table([
        {key: value for key, value in row.items() if key not in ("id", "faculty_id")}
        for row in rows
    ])

    if rows:
        with st.expander("Edit subject"):
            selected = st.selectbox(
                "Select subject",
                rows,
                format_func=lambda row: f"{row['Code']} - {row['Subject']}",
                key="edit_subject_select",
            )
            faculty_ids = list(faculty_options)
            selected_faculty = (
                selected["faculty_id"]
                if selected["faculty_id"] in faculty_options
                else None
            )
            with st.form("edit_subject"):
                code = st.text_input("Subject code", value=selected["Code"])
                name = st.text_input("Subject name", value=selected["Subject"])
                faculty_id = st.selectbox(
                    "Assigned faculty",
                    faculty_ids,
                    index=faculty_ids.index(selected_faculty),
                    format_func=lambda value: faculty_options[value],
                )
                submitted = st.form_submit_button("Save changes")
            if submitted:
                if not code.strip() or not name.strip():
                    st.error("Enter a subject code and name.")
                else:
                    try:
                        save_subject(
                            {"code": code, "name": name, "faculty_id": faculty_id},
                            selected["id"],
                        )
                        st.success("Subject updated.")
                    except sqlite3.IntegrityError:
                        st.error("Subject code already exists or faculty is invalid.")


def render_sessions(user):
    st.title("Class sessions")
    subjects = query_all(
        "SELECT s.id, s.code, s.name FROM subjects s "
        "JOIN faculty f ON f.id = s.faculty_id "
        "WHERE f.user_id = ? ORDER BY s.code",
        (user["id"],),
    )
    subject_options = {
        subject["id"]: f"{subject['code']} - {subject['name']}"
        for subject in subjects
    }
    rows = query_all(
        "SELECT cs.id, cs.subject_id, s.code AS Subject, "
        "cs.session_date AS Date, COALESCE(cs.topic, '') AS Topic, "
        "CASE WHEN EXISTS (SELECT 1 FROM attendance a "
        "WHERE a.class_session_id = cs.id) THEN 1 ELSE 0 END AS recorded "
        "FROM class_sessions cs JOIN subjects s ON s.id = cs.subject_id "
        "JOIN faculty f ON f.id = s.faculty_id "
        "WHERE f.user_id = ? ORDER BY cs.session_date DESC, cs.id DESC",
        (user["id"],),
    )

    if not subjects:
        st.info("Ask an administrator to assign a subject to your account.")
        return

    with st.expander("Add class session"):
        with st.form("add_session"):
            subject_id = st.selectbox(
                "Subject",
                list(subject_options),
                format_func=lambda value: subject_options[value],
            )
            session_date = st.date_input("Date", value=date.today())
            topic = st.text_input("Topic (optional)")
            submitted = st.form_submit_button("Add session", type="primary")
        if submitted:
            try:
                save_class_session(
                    {
                        "subject_id": subject_id,
                        "session_date": session_date.isoformat(),
                        "topic": topic.strip(),
                    },
                    user["id"],
                )
                st.success("Class session created.")
            except ValueError as error:
                st.error(str(error))

    show_table([
        {
            "Subject": row["Subject"],
            "Date": row["Date"],
            "Topic": row["Topic"] or "-",
            "Attendance": "Recorded" if row["recorded"] else "Not recorded",
        }
        for row in rows
    ])

    if rows:
        with st.expander("Edit class session"):
            selected = st.selectbox(
                "Select session",
                rows,
                format_func=lambda row: (
                    f"{row['Subject']} - {row['Date']} "
                    f"{'(' + row['Topic'] + ')' if row['Topic'] else ''}"
                ),
                key="edit_session_select",
            )
            subject_ids = list(subject_options)
            current_subject = (
                selected["subject_id"]
                if selected["subject_id"] in subject_options
                else subject_ids[0]
            )
            with st.form("edit_session"):
                subject_id = st.selectbox(
                    "Subject",
                    subject_ids,
                    index=subject_ids.index(current_subject),
                    format_func=lambda value: subject_options[value],
                )
                session_date = st.date_input(
                    "Date",
                    value=datetime.strptime(selected["Date"], "%Y-%m-%d").date(),
                )
                topic = st.text_input("Topic (optional)", value=selected["Topic"])
                submitted = st.form_submit_button("Save changes")
            if submitted:
                try:
                    save_class_session(
                        {
                            "subject_id": subject_id,
                            "session_date": session_date.isoformat(),
                            "topic": topic.strip(),
                        },
                        user["id"],
                        selected["id"],
                    )
                    st.success("Class session updated.")
                except ValueError as error:
                    st.error(str(error))

    if rows:
        with st.expander("Record or modify attendance"):
            selected = st.selectbox(
                "Select class session",
                rows,
                format_func=lambda row: f"{row['Subject']} - {row['Date']}",
                key="attendance_session_select",
            )
            render_attendance_form(selected)


def render_attendance_form(class_session):
    students = query_all(
        "SELECT id, roll_no, name FROM students ORDER BY roll_no"
    )
    current_rows = query_all(
        "SELECT student_id, status FROM attendance WHERE class_session_id = ?",
        (class_session["id"],),
    )
    current = {row["student_id"]: row["status"] for row in current_rows}
    if not students:
        st.info("Add students before recording attendance.")
        return

    with st.form(f"attendance_{class_session['id']}"):
        st.caption(
            f"{class_session['Subject']} | {class_session['Date']} "
            f"{class_session['Topic'] or ''}"
        )
        statuses = {}
        for student in students:
            label, roll, choice = st.columns([3, 2, 3])
            label.write(student["name"])
            roll.caption(student["roll_no"])
            statuses[student["id"]] = choice.radio(
                "Status",
                ("Present", "Absent"),
                index=0 if current.get(student["id"], "present") == "present" else 1,
                horizontal=True,
                key=f"attendance_{class_session['id']}_{student['id']}",
                label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Save attendance", type="primary")

    if submitted:
        with database() as db:
            db.executemany(
                "INSERT INTO attendance (class_session_id, student_id, status) "
                "VALUES (?, ?, ?) ON CONFLICT (class_session_id, student_id) "
                "DO UPDATE SET status = excluded.status",
                [
                    (class_session["id"], student_id, status.lower())
                    for student_id, status in statuses.items()
                ],
            )
        st.success("Attendance saved.")


def render_attendance_summary(user):
    st.title("Attendance summary")
    subjects = query_all(
        "SELECT s.id, s.code, s.name FROM subjects s "
        "JOIN faculty f ON f.id = s.faculty_id "
        "WHERE f.user_id = ? ORDER BY s.code",
        (user["id"],),
    )
    if not subjects:
        st.info("No subjects are assigned to your account.")
        return

    subject = st.selectbox(
        "Subject",
        subjects,
        format_func=lambda row: f"{row['code']} - {row['name']}",
    )
    rows = query_all(
        "SELECT st.roll_no AS SRN, st.name AS Name, "
        "COALESCE(SUM(a.status = 'present'), 0) AS Present, "
        "COUNT(a.id) AS Classes "
        "FROM students st "
        "LEFT JOIN (SELECT a2.* FROM attendance a2 "
        "JOIN class_sessions cs ON cs.id = a2.class_session_id "
        "WHERE cs.subject_id = ?) a ON a.student_id = st.id "
        "GROUP BY st.id ORDER BY st.roll_no",
        (subject["id"],),
    )
    for row in rows:
        row["Attendance"] = f"{attendance_percentage(row['Present'], row['Classes'])}%"
    show_table(rows, "No students to show.")


def render_my_attendance(user):
    st.title("My attendance")
    student = query_one(
        "SELECT id, roll_no, name FROM students WHERE user_id = ?", (user["id"],)
    )
    if student is None:
        st.error("No student profile is linked to this account.")
        return

    rows = query_all(
        "SELECT s.code AS Code, s.name AS Subject, "
        "COALESCE(SUM(a.status = 'present'), 0) AS Present, "
        "COUNT(a.id) AS Classes "
        "FROM subjects s "
        "LEFT JOIN class_sessions cs ON cs.subject_id = s.id "
        "LEFT JOIN attendance a ON a.class_session_id = cs.id "
        "AND a.student_id = ? "
        "WHERE EXISTS (SELECT 1 FROM attendance a2 "
        "JOIN class_sessions cs2 ON cs2.id = a2.class_session_id "
        "WHERE cs2.subject_id = s.id AND a2.student_id = ?) "
        "GROUP BY s.id ORDER BY s.code",
        (student["id"], student["id"]),
    )
    total_classes = sum(row["Classes"] for row in rows)
    total_present = sum(row["Present"] for row in rows)
    st.caption(f"{student['name']} · {student['roll_no']}")
    st.metric(
        "Overall attendance",
        f"{attendance_percentage(total_present, total_classes)}%",
    )
    for row in rows:
        row["Attendance"] = f"{attendance_percentage(row['Present'], row['Classes'])}%"
    st.subheader("By subject")
    show_table(rows, "No attendance has been recorded yet.")

    history = query_all(
        "SELECT cs.session_date AS Date, s.code AS Subject, "
        "COALESCE(cs.topic, '-') AS Topic, a.status AS Status "
        "FROM attendance a "
        "JOIN class_sessions cs ON cs.id = a.class_session_id "
        "JOIN subjects s ON s.id = cs.subject_id "
        "WHERE a.student_id = ? ORDER BY cs.session_date DESC, cs.id DESC",
        (student["id"],),
    )
    st.subheader("Recent classes")
    show_table(history, "No attendance history yet.")


def main():
    st.set_page_config(
        page_title="SAMS",
        page_icon="S",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        .stApp { background: #f5f8fa; }
        [data-testid="stMain"] > div { background: transparent; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #102a3a 0%, #163b4b 100%);
            border-right: 1px solid #244c5b;
        }
        [data-testid="stSidebar"] * { color: #e8f1f3; }
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #b7cbd0;
        }
        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(220, 235, 239, 0.16);
            border-radius: 12px;
            padding: 8px;
        }
        [data-testid="stSidebar"] .stButton > button {
            color: #f4fbfc !important;
            border-color: rgba(220, 235, 239, 0.18);
        }
        [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
            background: transparent;
        }
        [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
            background: #214958;
            border-color: #3a6874;
            color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {
            background: #0f766e;
            border-color: #0f766e;
            color: #ffffff !important;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #dce7ea;
            border-top: 3px solid #0f766e;
            padding: 18px 20px;
            border-radius: 12px;
            box-shadow: 0 4px 14px rgba(16, 42, 58, 0.05);
        }
        [data-testid="stForm"] {
            background: #ffffff;
            border: 1px solid #dce7ea;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 16px rgba(16, 42, 58, 0.04);
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #dce7ea;
            border-radius: 10px;
            overflow: hidden;
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 8px;
            font-weight: 600;
            transition: background-color 120ms ease, border-color 120ms ease;
        }
        h1, h2, h3 { color: #172b3a; }
        [data-testid="stCaptionContainer"] { color: #607783; }
        [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid #dce7ea;
            border-radius: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    initialize_database()
    user = st.session_state.get("user")
    if user is None:
        render_login()
        return

    with st.sidebar:
        st.title("SAMS")
        st.caption(f"{user['username']} · {user['role'].capitalize()}")
        pages = ["Dashboard"]
        if user["role"] == "admin":
            pages.extend(["Students", "Faculty", "Subjects"])
        elif user["role"] == "faculty":
            pages.extend(["Class sessions", "Students", "Faculty", "Attendance summary"])
        else:
            pages.append("My attendance")
        page = st.session_state.get("page", pages[0])
        if page not in pages:
            page = pages[0]
            st.session_state["page"] = page
        with st.container(border=True):
            for page_option in pages:
                if st.button(
                    page_option,
                    key=f"navigate_{page_option}",
                    type="primary" if page == page_option else "secondary",
                    width="stretch",
                ):
                    st.session_state["page"] = page_option
                    st.rerun()
        if st.button("Log out", type="primary", width="stretch"):
            st.session_state.clear()
            st.rerun()

    if page == "Dashboard":
        render_dashboard(user)
    elif page == "Students":
        render_students(user["role"])
    elif page == "Faculty":
        render_faculty(user["role"])
    elif page == "Subjects":
        render_subjects()
    elif page == "Class sessions":
        render_sessions(user)
    elif page == "Attendance summary":
        render_attendance_summary(user)
    elif page == "My attendance":
        render_my_attendance(user)


if __name__ == "__main__":
    main()
