# Study Tracker — Phase 2 frontend integration

## Files
Copy the files in this package into the root of your existing `study tracker` repository.
The existing `script.js` and `api-config.js` are intentionally unchanged.

## New pages
- `profile.html`: academic profile (GET/PUT `/api/profile/`)
- `syllabus.html`: chapter/topic CRUD and topic status updates
- `exams.html`: exam CRUD and upcoming/past filtering

## Updated existing files
- `index.html`, `today.html`, `progress.html`, `ideal.html`, `analysis.html`, `forecast.html`: added navigation links; dashboard has academic workspace shortcuts.
- `style.css`: added responsive styles for new pages.
- `academic.js`: new Phase 2 page logic.

## Before testing
1. Back up your local repository.
2. Confirm `api-config.js` points to a LOCAL development API, not production.
3. Serve the frontend from localhost (do not open HTML via `file://`).
4. Sign in with a test account and test profile, chapters, topics, and exams.
5. Do not push or deploy until local tests pass.

The frontend expects these API fields:
- Profile: `course`, `branch`, `academic_session`, `semester`, `daily_available_hours`
- Chapter: `subject`, `title`, `description`, `order`, optional `topic_count`
- Topic: `chapter`, `title`, `description`, `order`, `status`
- Exam: `subject`, `title`, `exam_date`, `priority`, `description`
Topic status values: `not_started`, `in_progress`, `completed`, `needs_revision`.
