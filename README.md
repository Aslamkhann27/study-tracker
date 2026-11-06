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


---

# Future Roadmap: Study Improvement System (SIS)

> **Status: Planned — these capabilities are part of the product roadmap and are not all implemented yet.**

## Product vision

Transform Study Tracker from a simple activity tracker into an intelligent study management platform that understands a student's syllabus, identifies learning gaps, creates personalized study plans, schedules revisions, and measures actual academic improvement.

The goal is not only to tell students how long they studied, but to help them understand how effective their preparation is and decide what to study next.

## Core system

The planned Study Improvement System will consist of five connected engines:

| Engine | Responsibility |
| --- | --- |
| Smart Study Analysis | Analyze syllabus coverage, pending topics, exam dates, and preparation status. |
| Weakness Detection | Identify weak subjects and topics using quiz results, accuracy, and repeated mistakes. |
| Automatic Study Planner | Generate and adjust personalized daily study plans. |
| Intelligent Revision | Schedule spaced repetition and prioritize topics that need more practice. |
| Performance Intelligence | Track readiness, subject-wise progress, and improvement over time. |

### Planned student workflow

1. Create an academic profile and add subjects.
2. Add chapters, topics, exam dates, and available study hours.
3. Review syllabus coverage and preparation status.
4. Attempt topic-based quizzes and practice tests.
5. Receive topic-level weakness analysis.
6. Get a personalized daily study plan.
7. Complete scheduled revisions and provide feedback.
8. Track readiness and improvement over time.

## Functional requirements

### 1. Smart Study Analysis

- Academic profile: course/degree, semester, academic session, subjects, exam dates, and daily available study hours.
- Subject and exam management, including exam date and priority.
- Hierarchical syllabus management: subject → chapter → topic.
- Topic states: Not Started, In Progress, Completed, and Needs Revision.
- Calculate total, completed, pending, and revision-required topics.
- Show syllabus completion percentage and days remaining until each exam.
- Preparation indicators: On Track, Needs Attention, At Risk, and Critical.
- Preparation status should consider exam deadlines and assessment performance, not syllabus completion alone.

### 2. Weakness Detection Engine

- Provide quizzes and tests with topic-linked questions.
- Planned question formats: MCQ, multiple select, true/false, and numerical questions.
- Record correct and incorrect answers, accuracy, time taken, and topic-wise performance.
- Identify strong topics and topics needing improvement.
- Track repeated mistakes and performance across multiple attempts.
- Compare performance before and after revision.
- Avoid permanently classifying a topic as weak based on a single small quiz.

Initial configurable classification thresholds:

| Accuracy | Initial classification |
| --- | --- |
| 90–100% | Strong |
| 75–89% | Good |
| 50–74% | Needs Improvement |
| Below 50% | Weak |

These are starting rules and should be calibrated using real usage and assessment data.

### 3. Automatic Study Planner

Generate personalized study plans using:

- Upcoming exam dates and deadlines.
- Pending syllabus and topic coverage.
- Topic difficulty and importance.
- Assessment-based weakness signals.
- Available study hours.
- Revisions that are due or overdue.

Planned capabilities:

- Daily and weekly study schedules with suggested durations.
- Prioritize urgent and weak topics.
- Reschedule incomplete tasks into available future slots.
- Preserve completed tasks when regenerating a plan.
- Let students add, edit, postpone, or manually prioritize tasks.
- Keep automatically generated tasks distinguishable from student-edited tasks.

### 4. Intelligent Revision System

- Use spaced-repetition scheduling after a topic is studied.
- Initial configurable revision intervals: 1, 3, 7, 14, and 30 days.
- Treat these intervals as defaults, not fixed scientific rules.
- Increase revision priority when quiz performance is poor or a topic is repeatedly missed.
- Let students mark revision feedback as Easy, Moderate, Difficult, or Still Not Understood.
- Adjust future revision timing using feedback and subsequent quiz performance.
- Show due, overdue, and upcoming revisions in a dedicated revision center.

### 5. Performance Intelligence

Measure learning and preparation quality rather than relying on study hours alone.

Planned dashboard metrics:

- Overall and subject-wise readiness.
- Syllabus completion.
- Quiz/test accuracy.
- Revision performance.
- Topic coverage and consistency.
- Strongest and weakest subjects/topics.
- Historical performance trends.
- Recommended next actions and exam-readiness indicators.

An initial readiness score may combine syllabus completion (20%), test accuracy (35%), revision performance (20%), topic coverage (15%), and consistency (10%). This is a heuristic starting point, not a validated prediction of exam marks. The score and weights must be evaluated and calibrated with real data. Do not present estimated marks as guaranteed outcomes.

## Planned supporting features

| Feature | Priority |
| --- | --- |
| Authentication and per-user data isolation | P0 — Must have |
| Academic profile and subject management | P0 — Must have |
| Topic-level syllabus and exam dates | P0 — Must have |
| Topic-linked question bank and quiz engine | P0 — Must have |
| Weakness analysis | P0 — Must have |
| Automatic daily planner | P0 — Must have |
| Basic revision scheduling | P0 — Must have |
| Syllabus CSV import | P1 — Important |
| Notifications and reminders | P1 — Important |
| Calendar and analytics visualizations | P1 — Important |
| Data export | P2 — Later |

## Planned technical direction

The existing application will be extended incrementally. The current frontend, Django REST API, PostgreSQL database, authentication, and deployed services should be reused wherever practical. Avoid a full rewrite unless an audit demonstrates a concrete need.

Potential backend modules (subject to an audit of the current codebase):

```text
backend/
├── accounts/
├── academics/       # subjects, syllabus, exams, chapters, topics
├── assessments/     # question bank, quizzes, attempts, answers
├── analytics/       # weakness analysis, readiness, trends
├── planner/         # study plans, tasks, scheduling
├── revision/        # revision schedules and history
└── dashboard/
```

Potential data entities to introduce or adapt after reviewing existing models:

- Exam, Chapter, and Topic
- Question, Quiz, QuizAttempt, and Answer
- TopicPerformance
- StudyPlan and StudyTask
- RevisionSchedule and RevisionHistory
- ReadinessSnapshot

Existing models and records should be preserved and extended through safe, reviewed database migrations. Model names and boundaries are proposals, not a commitment to duplicate entities that already exist.

## API direction

The following endpoints are proposed examples; final routes should follow the existing API conventions and be confirmed during implementation:

| Endpoint | Purpose |
| --- | --- |
| `/api/subjects/` | Manage subjects |
| `/api/syllabus/` | Manage chapters and topics |
| `/api/exams/` | Manage examinations |
| `/api/quizzes/` | List/create quizzes |
| `/api/quizzes/{id}/submit/` | Submit a quiz attempt |
| `/api/analytics/weakness/` | Topic and subject weakness analysis |
| `/api/analytics/readiness/` | Preparation/readiness analysis |
| `/api/planner/generate/` | Generate or regenerate a study plan |
| `/api/planner/today/` | Retrieve today's tasks |
| `/api/revision/due/` | Retrieve due revisions |
| `/api/revision/complete/` | Record a completed revision |
| `/api/dashboard/` | Retrieve the student dashboard |

## Development roadmap

| Phase | Scope | Priority |
| --- | --- | --- |
| 1. Foundation | Audit current code and database; academic profile; subjects, chapters, topics, syllabus states, and exam dates | Critical |
| 2. Assessment Engine | Topic-linked question bank, quizzes, automatic evaluation, and attempt history | Critical |
| 3. Weakness Detection | Topic accuracy, repeated mistakes, subject analysis, and improvement tracking | Critical |
| 4. Automatic Planner | Daily goals, scheduling priorities, exam deadlines, and dynamic rescheduling | Critical |
| 5. Intelligent Revision | Spaced repetition, weak-topic revision, feedback, and revision history | High |
| 6. Performance Intelligence | Readiness indicators, subject-wise trends, historical progress, and cautious exam-readiness estimates | High |

### MVP scope

The first usable release should include:

1. Student academic profile and subject management.
2. Syllabus management at topic level.
3. Exam date tracking.
4. Topic-based quizzes and assessment history.
5. Basic weakness detection.
6. Personalized daily study planning.
7. Basic revision scheduling.
8. A preparation/readiness dashboard.

An AI chatbot, advanced machine-learning predictions, PDF question extraction, and other advanced AI features are deferred until the core data and rule-based workflows are reliable.

## Non-functional requirements

- **Security:** Protect APIs and enforce ownership checks for every student's data.
- **Privacy:** Isolate student records; never expose one student's academic data to another.
- **Reliability:** Preserve study, assessment, and revision history.
- **Performance:** Keep dashboard and analytics queries efficient.
- **Maintainability:** Use clear, modular backend boundaries and documented APIs.
- **Compatibility:** Extend existing functionality without unnecessary rewrites or breaking changes.
- **Migrations:** Review schema changes and preserve existing production data.
- **Testing:** Add automated tests for calculations, permissions, planning, revision scheduling, APIs, and critical frontend flows.

## Success criteria

The system should be able to demonstrate that:

- Added syllabus topics are saved and correctly counted.
- Quiz submissions produce correct results and topic-level performance.
- Repeated poor performance identifies a topic for improvement.
- Exam deadlines influence study-plan priorities.
- Missed tasks can be rescheduled without losing completed work.
- Incorrect answers and weak topics can trigger appropriate revisions.
- Improved assessment results are reflected in performance trends.
- Readiness indicators are recalculated from recorded student activity and assessment data.

## Product principle

Study Tracker is intended to evolve into a **decision-making system**, helping students answer three questions every day:

1. **Where do I stand?** — How prepared am I?
2. **What should I study next?** — Which topic deserves my attention now?
3. **Am I improving?** — Is my actual understanding getting better?

All items in this section describe the future direction of the product. They should be marked as implemented in the README only after the corresponding functionality has been built and tested.
