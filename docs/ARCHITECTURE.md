# Architecture

## Request and data flow

```text
Browser
  | HTTPS: static HTML/CSS/JS
  v
GitHub Pages
  | script.js reads api-config.js
  | HTTPS JSON + Authorization: Bearer <JWT>
  v
Render: Django + Django REST Framework
  | /api/auth/register/
  | /api/auth/token/ and /api/auth/token/refresh/
  | /api/subjects/ and /api/entries/
  | /api/dashboard/ and /api/health/
  | server-side DATABASE_URL
  v
Neon PostgreSQL
```

The browser talks only to the HTTP API. PostgreSQL credentials remain on the backend host and are never required by the static frontend.

## Frontend

Root-level pages:
- `index.html`: dashboard
- `today.html`: daily plan
- `progress.html`: progress overview
- `analysis.html`: study analysis
- `forecast.html`: projections
- `ideal.html`: ideal schedule

`script.js` implements shared UI behavior, API calls and authentication. `api-config.js` sets `window.STUDY_API_BASE_URL`; absent that setting, the client falls back to `http://127.0.0.1:8000/api`.

The client stores tokens in local storage under `studyAccessToken` and `studyRefreshToken`. Requests include the access token as a Bearer token. On HTTP 401, the client attempts a refresh and retries the original request once.

## Backend modules

- `backend/config/settings.py`: Django apps, middleware, database, CORS, REST framework and JWT settings.
- `backend/config/urls.py`: admin, JWT endpoints and tracker routes.
- `backend/tracker/models.py`: `Subject` and `StudyEntry` data models.
- `backend/tracker/serializers.py`: registration and data validation/serialization.
- `backend/tracker/views.py`: registration, user-scoped viewsets, dashboard aggregates and health check.
- `backend/tracker/urls.py`: API route registration.

Protected endpoints require JWT authentication by default. Registration, token endpoints and health are public. Subject and entry querysets are scoped to the authenticated user; entry validation also checks that the selected subject belongs to that user.

## Data model

### Subject
- `user`: owning Django user (foreign key)
- `name`: subject name (maximum 100 characters)
- `created_at`: creation timestamp

A uniqueness constraint prevents duplicate subject names for the same user.

### StudyEntry
- `user`: owning Django user
- `subject`: related subject
- `study_date`: study date
- `target_hours`, `actual_hours`: decimal hour values
- `notes`: optional text (maximum 500 characters)
- `created_at`, `updated_at`: timestamps

A unique constraint allows one entry per user, subject and date. An index on `(user, study_date)` supports date-based user queries. Deleting a subject cascades to its entries.

## Dashboard logic

The dashboard aggregates today's and all-time target and actual hours. It groups study entries by date and calculates a consecutive streak backwards from the current local date. A day passes when actual hours are at least 80% of its target; the current implementation also passes a day with a non-positive target.

## Database

If `DATABASE_URL` is configured, Django uses `dj-database-url` to connect to PostgreSQL with a 600-second connection age. Otherwise, it uses `backend/db.sqlite3` for local development. Schema changes are managed through Django migrations.

## Security boundaries

- Frontend assets are public; no database credentials belong in them.
- API authorization and ownership checks are enforced server-side.
- CORS is controlled by `CORS_ALLOWED_ORIGINS`.
- Production secrets and database URLs must be configured in Render's environment settings and never committed.
