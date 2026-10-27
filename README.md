# Student Attendance Management System (SAMS)

**Team 2** | Software Engineering Mini-Project | Course Coordinator: Pavithra

A centralized, web-based system for recording, managing and monitoring student attendance, with role-based access for **Students**, **Faculty** and **Administrators**.

---

## Team Members

| Name | SRN | Role |
|---|---|---|
| Venkatesh | PES2UG24CS580 | Developer |
| Vishal | PES2UG24CS591 | Developer |
| Vummadisingu Sai Sri Saketh | PES2UG24CS602 | Test Engineer |
| Thejaswini | PES2UG24CS563 | QA Lead |

---

## Project Overview

SAMS lets faculty record and modify attendance for class sessions, lets students view their attendance status, history and percentage, and lets administrators manage students, faculty and subjects. Access to every function is restricted by user role.

### Key Features (SRS v1.0 scope)

- **Authentication and RBAC:** secure login, role-based access, invalid-login handling (SAMS-F-001 to F-003)
- **Student management:** add, update, view; block unauthorized edits (F-004 to F-007)
- **Faculty management:** add, update, view (F-008 to F-010)
- **Subject and class management:** manage subjects, view assigned subjects, manage class sessions (F-011 to F-013)
- **Attendance management:** record, modify, calculate percentage, view history (F-014 to F-017)
- **Non-functional and security requirements:** performance, availability, usability, reliability, maintainability, password hashing, data protection (SAMS-NFR-001 to NFR-006, SAMS-SR-001 to SR-005)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML + Jinja templates + CSS (server-rendered) |
| Backend | Python 3.10+ with Flask |
| Database | SQLite (relational) |
| Testing | pytest |
| CI/CD | GitHub Actions (lint + tests on every push and PR) |

The code follows the SAD's layered design: presentation (`src/templates`), application (`src/auth.py`, `students.py`, `faculty.py`, `subjects.py`) and data (`src/db.py`, `src/schema.sql`).

---

## Repository Structure

```
.
├── docs/              # SRS, SAD, Test Plan, DEVIATIONS.md
├── src/               # Application source code
├── tests/             # Test cases and scripts
├── demos/             # Sprint demo videos
├── .github/workflows/ # GitHub Actions CI
└── README.md
```

---

## Getting Started

```bash
# 1. Clone the repository
git clone <repo-url>
cd SE_miniproject

# 2. Create a virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Create the database (adds admin / admin123) and optional demo data
flask --app src init-db
flask --app src seed-demo        # faculty1/faculty123, student1/student123

# 4. Run the app, then open http://127.0.0.1:5000
flask --app src run --debug

# 5. Run the tests
pytest
```

---

## Project Management

Work is tracked in the GitHub Project **SAMS Backlog** linked to this repo.

| Sprint | Dates | Focus |
|---|---|---|
| Sprint 1 | 19 Oct - 23 Oct 2026 | Setup, authentication, RBAC, student/faculty/subject management |
| Sprint 2 | 26 Oct - 30 Oct 2026 | Class sessions, attendance, percentage, history, NFRs, documentation |

**Workflow**
1. Each backlog item is a GitHub Issue with story points, an assignee and a sprint.
2. The assignee works on a feature branch (e.g. `feature/SAMS-F-001-login`).
3. The assignee raises a Pull Request referencing the issue (`Closes #<issue>`).
4. A repo owner reviews and merges the PR.
5. GitHub Actions runs automated checks on every PR and push.

---

## Documentation

| Document | Location |
|---|---|
| Software Requirements Specification (SRS) | [`docs/`](docs/) |
| Software Architecture Document (SAD) | [`docs/`](docs/) |
| Software Test Plan (STP) | [`docs/`](docs/) |
| Deviations from submitted documents | [`docs/DEVIATIONS.md`](docs/DEVIATIONS.md) |

---

## Demos

| Sprint | Video |
|---|---|
| Sprint 1 (1 min) | _Link to be added in `demos/`_ |
| Sprint 2 (2 min) | _Link to be added in `demos/`_ |

---

## Scope Note

The Test Plan references additional features (QR/RFID attendance, notifications, leave management, reports) beyond SRS v1.0. This project implements the **SRS v1.0 scope**; any differences are recorded in `docs/DEVIATIONS.md`.

---

## License

For academic use only.
