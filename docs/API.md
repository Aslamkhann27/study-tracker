# API Reference

Production base URL: `https://study-tracker-backend-lt40.onrender.com/api`

Requests and responses use JSON. Protected endpoints require `Authorization: Bearer <access-token>`.

## Authentication

| Method | Path | Access | Purpose |
|---|---|---|---|
| POST | `/auth/register/` | Public | Create account |
| POST | `/auth/token/` | Public | Obtain JWT pair |
| POST | `/auth/token/refresh/` | Public | Refresh access token |
| POST | `/auth/logout/` | Authenticated | Blacklist a refresh token |

### Register
`POST /auth/register/`

```json
{ "username": "learner", "email": "learner@example.com", "password": "a-strong-password" }
```

Password must be at least 8 characters. The password is write-only.

### Login
`POST /auth/token/`

```json
{ "username": "learner", "password": "a-strong-password" }
```

Returns `access` and `refresh` JWTs. Access lifetime is 30 minutes and refresh lifetime is 7 days.

### Refresh
`POST /auth/token/refresh/`

```json
{ "refresh": "<refresh-token>" }
```

Refresh-token rotation is enabled.

### Logout
`POST /auth/logout/`

```json
{ "refresh": "<refresh-token>" }
```

The authenticated refresh token is blacklisted and can no longer be used.

## Authenticated resources

| Method | Path | Purpose |
|---|---|---|
| GET, POST | `/subjects/` | List or create own subjects |
| GET, PUT, PATCH, DELETE | `/subjects/{id}/` | Retrieve, update or delete own subject |
| GET, POST | `/entries/` | List or create own study entries |
| GET, PUT, PATCH, DELETE | `/entries/{id}/` | Retrieve, update or delete own entry |
| GET | `/dashboard/` | Current and all-time study aggregates |

### Create subject
`POST /subjects/`
```json
{ "name": "Data Structures" }
```

### Create study entry
`POST /entries/`
```json
{
  "subject": 1,
  "study_date": "2026-11-04",
  "target_hours": "2.00",
  "actual_hours": "1.50",
  "notes": "Practised linked lists"
}
```

The subject ID must belong to the authenticated user. The response includes read-only `subject_name`.

### Dashboard response
`GET /dashboard/` returns date, streak, today's totals, all-time totals and the current user's subjects. Shape:

```json
{
  "date": "2026-11-04",
  "streak": 1,
  "today": { "target_hours": "2.00", "actual_hours": "1.50" },
  "all_time": { "target_hours": "2.00", "actual_hours": "1.50" },
  "subjects": []
}
```

## Health
`GET /health/` is public and executes `SELECT 1` against the configured database.

Healthy: `200 { "status": "ok", "database": "ok" }`

Database failure: `503 { "status": "unhealthy", "database": "unavailable" }`

## Typical status codes
- `200`: successful read/update
- `201`: created
- `204`: deleted
- `400`: validation error
- `401`: missing or invalid authentication
- `404`: missing resource or resource outside the user's queryset
- `503`: database health check failed

No custom pagination settings are declared in the current REST framework configuration.
