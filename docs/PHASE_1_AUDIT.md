# Phase 1 — Existing Project Technical Audit

**Repository:** Aslamkhann27/study-tracker  
**Audited branch:** main  
**Date:** 2026-11-06  
**Status:** Static source/CI audit completed. Live Render/Neon configuration and local execution were not accessible, so those checks are explicitly unverified.

## Executive summary

The repository is a working small study-tracking application, not yet the planned Study Improvement System. It uses static HTML/CSS/vanilla JS, Django REST Framework, SimpleJWT, and PostgreSQL (Neon) in production with SQLite fallback locally.

The backend has one Django app (`tracker`) and two domain models (`Subject`, `StudyEntry`). It provides registration, JWT token/refresh/logout, subject CRUD, study-entry CRUD, dashboard aggregation, and a database health endpoint. No SIS academic profile, syllabus, exam, question bank, quiz, weakness analytics, planner, revision, or notification models/endpoints were found.

**Recommendation:** Extend the existing application with additive migrations. Do not rewrite the backend or reset the database.

## 1. Repository structure inspected

- Root static frontend: `index.html`, `today.html`, `progress.html`, `analysis.html`, `forecast.html`, `ideal.html`, `style.css`, `script.js`, `api-config.js`.
- Backend: `backend/config/`, `backend/tracker/`, `backend/manage.py`, `backend/requirements.txt`.
- Backend migrations: `0001_initial.py`, `0002_rename_...idx.py`.
- Tests: `backend/tracker/tests.py`, `tests/frontend.test.js`.
- Docs: `docs/ARCHITECTURE.md`, `docs/API.md`, `docs/DEPLOYMENT.md`.
- CI: `.github/workflows/backend-ci.yml`, `frontend-ci.yml`, `render-health-ping.yml`.

Backend responsibilities:
- `config/settings.py`: Django apps/middleware, DB, CORS/CSRF, security, DRF/JWT.
- `config/urls.py`: admin, token, refresh, logout and tracker route wiring.
- `tracker/models.py`: Subject and StudyEntry.
- `tracker/serializers.py`: registration and data validation.
- `tracker/views.py`: registration, logout, CRUD, dashboard, health.
- `tracker/urls.py`: API route registration.

## 2. Data model and migration audit

### Subject
- Owner FK to Django user; cascade delete.
- Name (max 100), created timestamp, ordered by name.
- Unique constraint on (user, name).

### StudyEntry
- Owner FK and Subject FK; both cascade delete.
- Study date, target/actual decimal hours (2 decimal places), optional notes (max 500), created/updated timestamps.
- Unique constraint on (user, subject, study_date).
- Index on (user, study_date).
- One entry per subject per student per day; multiple study sessions must currently be combined.

### Migrations
- 0001 creates Subject and StudyEntry, constraints and index.
- 0002 renames the StudyEntry index.
- No models/tables for academic sessions, semesters, chapters, topics, exams, questions, quizzes, attempts, plans, tasks, revision, or readiness snapshots.

### Integrity notes
- API serializer rejects negative hours and subjects belonging to another user.
- No database-level invariant currently guarantees StudyEntry.user matches StudyEntry.subject.user for writes outside the API serializer (e.g. admin/scripts).
- Deleting a Subject cascades and deletes its StudyEntry history; preserve/confirm this policy before adding archival academic history.
- Existing migration history should remain intact; future SIS schema work should be additive and reviewed.

## 3. API and authentication audit

| Method | Route | Access | Purpose |
|---|---|---|---|
| POST | /api/auth/register/ | Public | Register |
| POST | /api/auth/token/ | Public | Obtain JWT pair |
| POST | /api/auth/token/refresh/ | Public | Refresh access |
| POST | /api/auth/logout/ | Authenticated | Blacklist refresh token |
| GET/POST | /api/subjects/ | Authenticated | List/create own subjects |
| CRUD | /api/subjects/{id}/ | Authenticated | Manage own subject |
| GET/POST | /api/entries/ | Authenticated | List/create own entries |
| CRUD | /api/entries/{id}/ | Authenticated | Manage own entry |
| GET | /api/dashboard/ | Authenticated | Aggregates and subjects |
| GET/HEAD | /api/health/ | Public | Database check |

JWT settings: 30-minute access, 7-day refresh, rotation enabled, blacklist after rotation. DRF defaults to IsAuthenticated. Registration uses Django create_user and password validation.

**Strengths**
- Subject and StudyEntry querysets are filtered to request.user.
- Entry serializer validates subject ownership.
- Tests cover cross-user list/detail isolation and cross-user subject assignment rejection.

**Security findings**
1. **High — logout token ownership:** Logout authenticates the caller but blacklists the supplied refresh token without checking that its user claim matches request.user. Validate ownership and add a regression test.
2. **Medium — localStorage tokens:** Frontend stores access and refresh JWTs in localStorage. XSS could expose them. Evaluate secure HttpOnly same-site cookie/BFF design before frontend migration; otherwise document mitigations and threat model.
3. **Medium — no DRF throttling:** Add scoped limits for registration, token/login and refresh endpoints.
4. **High — production HTTPS unverified:** SECURE_SSL_REDIRECT defaults False. Explicitly configure production HTTPS and verify Render proxy SSL-header behavior before enabling redirect to avoid loops.
5. **Medium — CORS/CSRF environment:** Defaults are local origins; verify exact production origins in Render, no wildcard credentials.
6. **Medium — limited diagnostics:** Public health returns generic 503 on exception, but server-side structured logs are needed for diagnosis.

These are source-review risks, not proof of a known exploit or confirmed production misconfiguration.

## 4. Frontend/backend communication

- Static frontend hosted on GitHub Pages; API documented on Render; database Neon.
- `api-config.js` defines production API base.
- `script.js` wraps fetch, adds Bearer token, refreshes/retries once after 401, clears tokens on refresh failure.
- Frontend loads subjects, entries and dashboard through separate calls.
- Token storage is localStorage.
- API helper supports array or paginated `results`, but current DRF settings do not configure pagination.
- No React/Vite app exists in the audited tree.
- The client currently loads the complete entry list; add pagination/date/subject filters as history grows.
- API paths are string-coupled in script.js; document contract changes and coordinate frontend changes.
- No explicit API version prefix or standardized error envelope exists.

## 5. Dashboard/business logic observations

Dashboard aggregates today and all-time target/actual hours, returns subjects, and computes a streak by walking backward from today's local date.

Current streak semantics:
- A day passes at actual >= 80% of target.
- Non-positive target is treated as passing.
- Missing entry for today yields zero streak even if yesterday qualified.
- These rules are implicit and not covered by dedicated edge-case tests.

Before SIS analytics, define behavior for today not yet studied, rest days, zero targets, timezone, and corrected historical entries; then test boundaries.

## 6. Tests and CI evidence

### Tests present
Django tests cover subject creation/list scoping, entry creation, negative-hour rejection, logout blacklist, cross-user data isolation, dashboard authentication, and public DB-aware health response. Frontend Node test covers local date formatting.

### CI workflows
- Backend CI: install requirements, Django check, migration drift check, apply migrations, run Django tests.
- Frontend CI: npm test.
- Render health ping: scheduled and manual curl to production health endpoint.

### Observed GitHub Actions runs
- Backend CI and Frontend CI passed on main code snapshot commit `d8b2f5e1...` on 2026-11-03.
- Current main later received a documentation-only README roadmap commit; no application code changes were in that commit.
- Latest inspected scheduled health run `42149518855` on 2026-11-06 failed: curl timed out after 20 seconds with zero response bytes. Several earlier scheduled pings also failed; a manual ping on 2026-11-03 succeeded.
- This confirms a timeout during that check, not its root cause. Investigate Render events/logs, cold starts, service health and DB connectivity.

### Verification limits
This was a GitHub source and CI-record audit. It did **not** run a local checkout, connect to Neon, inspect Render environment variables, execute production migrations, or complete browser-based registration/login/CRUD smoke tests. A live health request was not accessible in this inspection environment. Those checks are not marked passed.

## 7. Findings register

| ID | Finding | Priority | Action |
|---|---|---|---|
| AUD-01 | Logout does not verify refresh-token owner | P0 | Validate token user claim; regression tests |
| AUD-02 | No API throttling | P0/P1 | Scoped auth throttles |
| AUD-03 | localStorage JWT risk | P1 | Threat model and token-storage decision |
| AUD-04 | Production HTTPS/proxy behavior unverified | P0 | Verify Render settings and redirect behavior |
| AUD-05 | Scheduled health pings time out | P0 operational | Diagnose Render/DB; monitor latency |
| AUD-06 | No pagination/filtering | P1 | Add with compatible client changes |
| AUD-07 | CRUD/constraint/boundary tests incomplete | P1 | Expand regression suite |
| AUD-08 | Streak edge cases untested | P1 | Define semantics and test |
| AUD-09 | Owner/subject invariant only serializer-enforced | P1 | Centralize invariant; consider DB enforcement |
| GAP-01 | No academic profile/session | SIS gap | Academics domain |
| GAP-02 | No chapter/topic syllabus | SIS gap | Syllabus domain |
| GAP-03 | No exams | SIS gap | Exam domain |
| GAP-04 | No question bank/quiz attempts | SIS gap | Assessment domain |
| GAP-05 | No weakness/readiness analytics | SIS gap | Analytics after assessment data |
| GAP-06 | No automatic planner | SIS gap | Planner after academics/analytics |
| GAP-07 | No revision engine | SIS gap | Revision domain |
| GAP-08 | No notification service | SIS gap | Later supporting service |
| GAP-09 | No SIS dashboard aggregation | SIS gap | After domain services |

## 8. Existing functionality to preserve

- User accounts and password hashes.
- Existing Subject and StudyEntry rows.
- Subject uniqueness and daily-entry uniqueness.
- Current auth/token contract, except security hardening with compatible behavior where possible.
- Existing subject/entry CRUD.
- Existing dashboard fields until compatible extension/versioning is agreed.
- Production PostgreSQL database and migration history.

Do not rename/drop tables, reset production data, or rewrite the frontend in Phase 1.

## 9. Phase 1 exit criteria and local commands

**Source audit and documentation deliverables: complete.** Phase 1 is a baseline, not SIS implementation.

Before Phase 2:
- Review target architecture and priorities.
- Address or explicitly accept P0 security/operational issues.
- Confirm production backup and restore procedure.
- Run local checks in a real checkout.
- Investigate health timeout with Render access.
- Agree to additive migrations and API compatibility.

From `backend/`:
```bash
python -m pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate --plan
python manage.py test --verbosity 2
```

From repository root:
```bash
npm ci
npm test
```

Do not run production migrations against Neon until backup/restore and deployment window are confirmed.
