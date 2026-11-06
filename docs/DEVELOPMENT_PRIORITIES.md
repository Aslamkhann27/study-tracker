# Phase 1 — Development Priorities and Execution Backlog

Priorities are based on the audited source. P0 must be addressed before core SIS implementation or production exposure; P1 hardens the foundation; P2 builds SIS; P3 is later.

## P0 — Security and operational baseline

| ID | Work | Acceptance / verification |
|---|---|---|
| SEC-01 | Verify refresh token belongs to authenticated user on logout | Cross-user token blacklist rejected; own logout still passes; API regression tests |
| SEC-02 | Verify production HTTPS and Render proxy behavior | HTTPS works without redirect loop; headers and settings verified in staging |
| OPS-01 | Investigate recurring Render health ping timeouts | Render logs/events and DB path inspected; root cause or bounded mitigation documented |
| OPS-02 | Confirm database backup and restore | Restore tested to non-production DB; row counts validated |
| SEC-03 | Add scoped API throttling | Auth endpoints rate-limited; normal use and throttle response tested |

## P1 — Existing backend hardening

| ID | Work | Acceptance / verification |
|---|---|---|
| API-01 | Add entry pagination and date/subject filters | Stable ordering and filters tested; client compatibility documented |
| API-02 | Standardize error response format | Validation/auth/not-found contract tests |
| DATA-01 | Enforce StudyEntry/Subject owner consistency outside serializer | Admin/service paths cannot create mismatched owners; tests |
| DATA-02 | Decide subject deletion vs archive policy | Historical study data behavior documented and tested |
| TEST-01 | Expand CRUD/constraint tests | Update/delete, duplicate subject/date, decimal bounds, invalid date tested |
| TEST-02 | Define streak semantics | Today missing, yesterday qualifying, zero target, rest day, timezone covered |
| AUTH-01 | Decide future token-storage strategy | HttpOnly cookie/BFF vs localStorage threat model documented |
| LOG-01 | Add structured server-side diagnostics | Failures diagnosable without leaking credentials/tokens |

## P2 — SIS foundation and product

| ID | Work | Acceptance / verification |
|---|---|---|
| SIS-01 | Academic profile and sessions | CRUD and ownership tests |
| SIS-02 | Subject compatibility mapping | Existing subject records preserved in migration tests |
| SIS-03 | Chapter/topic syllabus | CRUD, order, status, difficulty, importance; ownership tests |
| SIS-04 | Exam schedule | Date validation, subject association, countdown service tests |
| SIS-05 | Question bank | Supported formats, answer key privacy, topic mapping tests |
| SIS-06 | Quiz attempts/history | Server scoring, retakes, immutable attempt history |
| SIS-07 | Weakness/performance | Evidence thresholds and historical trend service tests |
| SIS-08 | Study planner | Exam, topic, availability and weakness inputs produce explainable tasks |
| SIS-09 | Revision scheduler | Due/overdue, feedback, history and adaptive intervals tested |
| SIS-10 | Dashboard aggregation | Metrics derived from real data; integration tests |

## P3 — Later enhancements
- Notifications (email/browser/push) after event rules/preferences exist.
- Syllabus/question CSV import/export with row-level error reports.
- OpenAPI/Swagger and API versioning.
- Background workers only when reminders or expensive jobs need them.
- Student data export and account deletion.
- Advanced ML only after enough high-quality assessment data exists.

## Recommended sequence
1. Close P0 security/operations.
2. Complete P1 API/data/test hardening.
3. Design academics model and migration compatibility.
4. Implement syllabus and exams.
5. Implement question bank and quiz engine.
6. Implement analytics and weakness detection.
7. Implement planner and revision.
8. Implement dashboard and notifications.
9. Freeze API contracts; then redesign frontend.

## Definition of done
A task is not complete just because code is committed. Require reviewed models/migrations, normal/invalid/boundary/cross-user tests, updated API docs, passing Django checks and migration drift check, passing relevant CI, staging smoke tests, and evidence that existing student records remain intact.

## Phase 1 non-goals
No SIS feature models/endpoints, frontend rewrite, production schema changes, direct Neon mutation, or claims of live/browser verification without evidence.
