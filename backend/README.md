# Study Tracker API (Django)

This backend is added alongside the existing plain HTML/CSS/JavaScript frontend. The frontend now includes login/registration and reads and writes study data through this API. It remains plain HTML/CSS/JavaScript.

## Local setup

From the repository root:

```powershell
cd backend
py -m venv .venv
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py makemigrations tracker
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

On macOS/Linux, activate with `source .venv/bin/activate` and copy the env file with `cp .env.example .env`.

API base URL: `http://127.0.0.1:8000/api/`. The frontend reads this from the root `api-config.js` file. Change `window.STUDY_API_BASE_URL` there to your deployed API URL before publishing the frontend.

## Endpoints

- `POST auth/register/` — create account (`username`, `email`, `password`, minimum 8 characters)
- `POST auth/token/` — get JWT tokens (`username`, `password`)
- `POST auth/token/refresh/` — refresh access token
- `GET/POST subjects/` — list/create your subjects
- `GET/PUT/PATCH/DELETE subjects/{id}/` — manage your subjects
- `GET/POST entries/` — list/create study records
- `GET/PUT/PATCH/DELETE entries/{id}/` — manage study records
- `GET dashboard/` — today's totals, all-time totals, streak and subjects
- `GET health/` — public database-aware health check; returns 503 if database is unavailable

All endpoints except registration and token issuance require `Authorization: Bearer <access>`. Users can only see and modify their own subjects and study entries.

## Deployment (Render)

Create a Python web service with root directory `backend`.

Build command:
```bash
pip install -r requirements.txt && python manage.py migrate
```

Start command:
```bash
gunicorn config.wsgi:application
```

Set `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=<your-render-hostname>`, `DATABASE_URL=<PostgreSQL-internal-connection-string>`, and `CORS_ALLOWED_ORIGINS=<your-frontend-origin>`. Never commit real secrets. Use a persistent PostgreSQL database in production; SQLite is only the local development fallback.

## Free uptime ping (GitHub Actions)

The workflow at `.github/workflows/render-health-ping.yml` calls `/api/health/` every 5 minutes. Scheduled workflows run from the repository default branch, so this starts only after the workflow is merged into `main`. It uses GitHub Actions' free allowance. Set the repository Actions variable `RENDER_HEALTH_URL` to the deployed health URL, e.g. `https://YOUR-SERVICE.onrender.com/api/health/`. This is best-effort only: scheduled runs can be delayed, and Render may still suspend or restart a free service; uptime is not guaranteed.

## Current status

Backend API scaffold and basic API tests are committed on the feature branch. Run migrations and tests locally before deployment. The legacy frontend still uses browser LocalStorage until API integration is completed.
