# Deviations from Submitted Documents

Record every difference between what was submitted (SRS, SAD, Test Plan) and what was built.
These will be explained during the final demo.

| # | Document / Section | Document says | What we built | Reason |
|---|---|---|---|---|
| 1 | Test Plan, sections 1-3 | Covers QR/RFID attendance, notifications, leave/on-duty, reports, correction approval, 5 roles (F-020 to F-062) | Only SRS v1.0 scope: F-001 to F-017, NFR-001 to 006, SR-001 to 005; 3 roles | Test Plan features are not in the SRS; two-week time limit |
| 2 | Test Plan, NFRs | 90% of requests in 3 s; 99.5% availability; WCAG 2.1 AA; 3-year retention | SRS values used: 95% in 3 s; 99% availability | SRS is the source of truth |
| 3 | SAD 4.3 (API design) | REST endpoints such as `/api/auth/login`, `/api/students` | Server-rendered pages: `/login`, `/students/`, `/faculty/`, `/subjects/` | SAD says endpoint names may be changed; simpler for a two-week build |
| 4 | SAD 3.9 (technology) | Stack TBD | Python Flask + SQLite + Jinja templates + pytest | Chosen by team; fits the layered design |
| 5 | SRS 3.4 (HTTPS) | HTTPS between client and server | Development server uses HTTP | HTTPS to be provided by the deployment environment; not set up for the demo |
| 6 | SAD 4.6 (data design) | Faculty-Subject Mapping entity | Stored as `faculty_id` on `subjects` (one faculty per subject) | Simpler schema; sufficient for F-012 |
| 7 | Sprint plan | Sprint 1: 19-23 Oct | Sprint 1 work started late (TODO: add actual dates) | Backlog and setup completed late |
| 8 | Team | 4 members | TODO: list who contributed, if fewer than 4 | |

## Known limitations (not in the SRS)
- No CSRF tokens on forms.
- Default admin password (`admin123`) must be changed before any real use.
