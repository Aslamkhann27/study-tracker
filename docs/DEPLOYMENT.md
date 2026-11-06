# Deployment Guide

## Hosting topology

| Component | Provider | Notes |
|---|---|---|
| Static frontend | GitHub Pages | Repository root |
| Django API | Render | Python web service |
| PostgreSQL | Neon | Production database |
| CI | GitHub Actions | Backend checks and health ping |

Frontend: `https://aslamkhann27.github.io/study-tracker/`

API host: `https://study-tracker-backend-lt40.onrender.com`

## Render configuration

Build command:

```bash
cd backend && pip install -r requirements.txt && python manage.py migrate --noinput
```

Start command:

```bash
cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Configure these variables in the Render dashboard. Do not put secret values in Git:

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Strong unique Django secret |
| `DEBUG` | `False` in production |
| `ALLOWED_HOSTS` | Include the Render hostname |
| `CORS_ALLOWED_ORIGINS` | Exact deployed frontend origin |
| `CSRF_TRUSTED_ORIGINS` | Exact HTTPS origins allowed for Django CSRF checks |
| `SECURE_SSL_REDIRECT` | `True` in production |
| `DATABASE_URL` | Neon PostgreSQL connection URL |

The scheduled Render health-ping workflow accepts the optional repository
Actions variable `RENDER_HEALTH_URL`. When it is not configured, it safely
checks the public production endpoint
`https://study-tracker-backend-lt40.onrender.com/api/health/`.
The probe retries transient connection, timeout and HTTP failures for up to
two minutes so a cold-starting Render service does not cause a false failure.

The application falls back to SQLite only when `DATABASE_URL` is absent. Production should use Neon. Render runs migrations during each build before starting Gunicorn.

## Neon

The Django process connects to Neon using the server-side `DATABASE_URL`. Never put this URL in `api-config.js`, frontend source, public issues or logs. Review and apply schema changes through Django migration files under `backend/tracker/migrations`.

## GitHub Pages

The committed `api-config.js` sets the public API base URL:

```js
window.STUDY_API_BASE_URL = "https://study-tracker-backend-lt40.onrender.com/api";
```

This endpoint URL is not secret. Ensure the exact GitHub Pages origin is included in Django's `CORS_ALLOWED_ORIGINS`.

For local development, run Django from `backend` with `python manage.py runserver`, and serve the repository root with `python -m http.server 5500`. Point the frontend API base to `http://127.0.0.1:8000/api`.

## Release checklist

1. Review source changes and migrations.
2. Confirm GitHub Actions checks pass.
3. Merge the pull request into `main`.
4. Confirm Render build and deployment succeed.
5. Verify `/api/health/` returns healthy status.
6. In a browser, test registration, login, token refresh, subject CRUD and study-entry CRUD.
7. Verify data persists after refresh and is isolated between two test accounts.

Production settings reject a missing `SECRET_KEY` when `DEBUG=False`, enable
secure cookie and HSTS defaults, and blacklist refresh tokens on logout and
rotation.

A live service/deploy does not alone prove all browser flows. Perform the browser smoke tests before declaring a release fully validated.
