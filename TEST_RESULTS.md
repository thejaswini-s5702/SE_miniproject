# Test Results (maps SRS requirements to automated tests)

Run all tests with `pytest`. GitHub Actions runs them on every pull request.

| Requirement | Test case ID | Automated tests in | Result |
|---|---|---|---|
| SAMS-F-001 User authentication | TC-Auth-01 | `tests/test_login.py` | Passed |
| SAMS-F-002 Role-based access | TC-Auth-02 | `tests/test_rbac.py` | Passed |
| SAMS-F-003 Invalid login handling | TC-Auth-03 | `tests/test_login.py` | Passed |
| SAMS-F-004 Add student | TC-Student-01 | `tests/test_student_add.py` | Passed |
| SAMS-F-005 Update student | TC-Student-02 | `tests/test_student_edit.py` | Passed |
| SAMS-F-006 View student | TC-Student-03 | `tests/test_student_access.py` | Passed |
| SAMS-F-007 Block unauthorized edits | TC-Student-04 | `tests/test_student_access.py` | Passed |
| SAMS-F-008 Add faculty | TC-Faculty-01 | `tests/test_faculty_add.py` | Passed |
| SAMS-F-009 Update faculty | TC-Faculty-02 | `tests/test_faculty_edit.py` | Passed |
| SAMS-F-010 View faculty | TC-Faculty-03 | `tests/test_faculty_add.py` | Passed |
| SAMS-F-011 Manage subjects | TC-Subject-01 | `tests/test_subjects_admin.py` | Passed |
| SAMS-F-012 View assigned subjects | TC-Subject-02 | `tests/test_subjects_mine.py` | Passed |
| SAMS-F-013 Manage class sessions | TC-Class-01 | `tests/test_class_sessions.py` | Passed |
| SAMS-F-014 Record attendance | TC-Attendance-01 | `tests/test_attendance_record.py` | Passed |
| SAMS-F-015 Modify attendance | TC-Attendance-02 | `tests/test_attendance_modify.py` | Passed |
| SAMS-F-016 Attendance percentage | TC-Attendance-03 | `tests/test_attendance_percentage.py` | Passed |
| SAMS-F-017 Student views attendance | TC-Attendance-04 | `tests/test_student_attendance.py` | Passed |
| SAMS-SR-001 Login required | TC-Sec-01 | `tests/test_login.py` | Passed |
| SAMS-SR-002 Role-based access | TC-Sec-02 | `tests/test_rbac.py` | Passed |
| SAMS-SR-003 Students cannot modify attendance | TC-Sec-03 | `tests/test_attendance_modify.py`, `tests/test_attendance_record.py` | Passed |
| SAMS-SR-004 Hashed passwords | TC-Sec-04 | `tests/test_login.py` | Passed |
| SAMS-SR-005 Protect attendance and user data | TC-Sec-05 | `tests/test_student_attendance.py` | Passed |
| SAMS-NFR-004 Consistent navigation | TC-NFR-04 | `tests/test_rbac.py` (role dashboards) | Passed |
| SAMS-NFR-005 Data accuracy and integrity | TC-NFR-05 | `tests/test_attendance_record.py` (all-or-nothing save) | Passed |
| SAMS-NFR-006 Modular components | TC-NFR-06 | Code structure: one Flask blueprint per module | Reviewed |
| SAMS-NFR-001, 002, 003 Performance and availability | TC-NFR-01 to 03 | Not load-tested | See `docs/DEVIATIONS.md` |
