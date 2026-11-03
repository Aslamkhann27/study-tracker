# Study Tracker

A lightweight, browser-based dashboard for planning and reviewing study progress.

## Run locally

This project is a static website, so no package installation or build step is required:

1. Clone the repository and open its folder.
2. Start a local static server from that folder, for example:
   ```powershell
   python -m http.server 8000
   ```
3. Visit `http://localhost:8000` in a browser and open `index.html` if it is not loaded automatically.

You can also open `index.html` directly, but a local server provides more reliable browser behavior for local assets.

## Pages

- **Home**: dashboard with today's target, tasks, and current streak.
- **Progress**: review study progress.
- **Today**: manage the current day's study plan.
- **Ideal**: view the ideal study plan.
- **Analysis** and **Forecast**: inspect study trends and projections.

The site is implemented with plain HTML, CSS, and JavaScript. Changes to the files are reflected by refreshing the browser.

## Data and production scope

This project is currently a client-only prototype. Study data is stored in the browser's
`localStorage`; there is no backend, account system, JWT authentication, database,
server-side authorization, or deployment configuration in this repository. Do not use
the app for sensitive data or treat browser storage as a synchronized backup.

The browser app validates and sanitizes stored values before using them. For a
multi-user production deployment, add a server-side API and database, then implement
authentication, per-user authorization, HTTPS, a restrictive Content Security Policy,
CSRF protection where applicable, rate limiting, backups, and monitoring before
storing personal data.
