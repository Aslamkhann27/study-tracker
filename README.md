# Study Tracker

A browser-based study tracker with a static HTML/CSS/JavaScript frontend and a Django REST API backed by PostgreSQL.

## Live application
- **Frontend:** https://aslamkhann27.github.io/study-tracker/
- **Backend API:** https://study-tracker-backend-lt40.onrender.com/api/
- **Health check:** https://study-tracker-backend-lt40.onrender.com/api/health/

The frontend is hosted on GitHub Pages, the API on Render, and production data is stored in Neon PostgreSQL.

## Features
- User registration and login with JWT authentication.
- Per-user subjects and daily study entries.
- Daily targets, actual study hours, progress, analysis and forecast pages.
- Dashboard summaries for today's totals, all-time totals and study streak.
- Persistent API-backed data across devices when signed in.

## Technology
HTML, CSS, vanilla JavaScript, Python, Django, Django REST Framework, SimpleJWT, Neon PostgreSQL, GitHub Pages, Render and GitHub Actions.

## Repository layout
```text
.
├── index.html, today.html, progress.html
├── analysis.html, forecast.html, ideal.html
├── style.css, script.js, api-config.js
├── backend/
│   ├── config/       # Django settings and root URL routing
│   ├── tracker/      # Models, serializers, API views and routes
│   └── requirements.txt
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── DEPLOYMENT.md
└── .github/workflows/
```

## Run locally

### Backend
Python 3.10+ recommended.

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The API runs at `http://127.0.0.1:8000/api/`. If `DATABASE_URL` is not set, Django uses local SQLite.

### Frontend
From the repository root:

```bash
python -m http.server 5500
```

Open `http://localhost:5500`. For local testing, configure `window.STUDY_API_BASE_URL` in `api-config.js` to `http://127.0.0.1:8000/api`. The committed production config points to Render.

## Documentation
- [Architecture](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Deployment guide](docs/DEPLOYMENT.md)

## Security
- Never commit `SECRET_KEY`, database URLs, passwords or other credentials.
- Set a strong `SECRET_KEY`, `DEBUG=False`, and restrictive `ALLOWED_HOSTS` in production.
- Restrict `CORS_ALLOWED_ORIGINS` to the deployed frontend origin.
- Keep `DATABASE_URL` server-side in Render; never expose it to browser code.
- The current frontend stores JWT tokens in browser local storage.

## Validation
Frontend CI runs the Node-based smoke test, while backend CI runs Django checks,
migration checks, and the API test suite. A successful deployment confirms the
service starts, but browser-based registration/login and subject/study-entry CRUD
smoke tests should also be completed before treating a release as fully verified.
