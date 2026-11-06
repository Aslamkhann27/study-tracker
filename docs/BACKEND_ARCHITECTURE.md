# Proposed Backend Architecture — Study Improvement System

**Status:** Target design proposal based on Phase 1 audit. The modules/models below are not implemented yet.

## Principles
- Extend the current DRF service; avoid a rewrite.
- Preserve tracker.Subject and tracker.StudyEntry and their API contract.
- Use additive/reviewed migrations.
- Put business rules in domain services/selectors, not oversized views.
- Enforce owner scoping at queryset, serializer/service and feasible DB layers.
- Derive analytics from source records; snapshot only when needed.
- Readiness is an explainable heuristic, not guaranteed exam-score prediction.
- Build domains in dependency order.

## Target architecture

```text
Browser / future React client
          | HTTPS + API auth
          v
Django REST Framework (modular monolith)
  accounts       profile/preferences
  academics      sessions/semesters/subjects/chapters/topics
  exams          exam schedule
  assessments    question bank/quizzes/attempts/answers
  analytics      weakness/readiness/performance trends
  planner        plans/tasks/scheduling
  revision       revision schedules/history/feedback
  notifications  preferences/notifications/delivery
  tracker        legacy Subject/StudyEntry compatibility
          |
          v
PostgreSQL (current production: Neon)

Optional future worker: reminders, long-running plan generation, periodic snapshots.
Introduce Celery/Redis only when real asynchronous workloads justify them.
```

## Proposed app boundaries

| App | Responsibility | Dependencies |
|---|---|---|
| accounts | Student profile/preferences, auth extensions | Django auth |
| academics | AcademicSession, Semester, Subject, Chapter, Topic | accounts |
| exams | Exam and schedule | academics |
| assessments | Question, Quiz, QuizQuestion, QuizAttempt, Answer | academics |
| analytics | TopicPerformance, snapshots, weakness/readiness services | academics, assessments, revision |
| planner | StudyPlan, StudyTask, scheduling services | academics, exams, analytics, revision |
| revision | RevisionSchedule, RevisionHistory, feedback | academics, assessments |
| notifications | Notification, preferences, delivery adapters | accounts, exams, planner, revision |
| tracker | Existing Subject/StudyEntry compatibility boundary | Django auth |

**Do not create a duplicate Subject model by default.** Phase 2 must decide whether tracker.Subject is extended in place or safely mapped into the academic hierarchy. Preserve existing rows either way.

## Logical relationship proposal

```text
User -> StudentProfile -> AcademicSession -> Semester -> Subject
Subject -> Chapter -> Topic -> Question
Topic -> TopicPerformance / RevisionSchedule
Subject -> Exam
Quiz -> QuizQuestion -> Question
QuizAttempt(user, quiz, timestamps, score) -> Answer(attempt, question, response, correctness)
StudyPlan(user, date/range) -> StudyTask(topic, duration, status, source)
RevisionSchedule -> RevisionHistory
ReadinessSnapshot(user, scope, calculated_at, component scores)
Notification(user, type, payload, read_at)
```

This is logical only. Field types, constraints, deletion policies and exact relations must be designed before migrations.

## Domain invariants

### Ownership and hierarchy
- Every student-owned record has exactly one owner directly or through an owned parent.
- A topic's chapter and subject must belong to the same student.
- An exam must reference a subject in the same academic scope.
- Quiz attempts and answers belong to the authenticated user.
- Never trust client-supplied user/owner IDs.

### Assessment
- Submitted attempts are immutable; retakes create new attempts.
- Correct answers/scoring stay server-side until submission.
- Multiple-select scoring rules are explicit.
- Questions must link to eligible topics.

### Planner and revision
- Automatic regeneration must not delete completed tasks.
- Generated tasks and student-edited tasks are distinguishable.
- Scheduling respects availability and exam deadlines.
- Every revision completion creates history; changing next due date must not erase history.

### Analytics
- Define denominator and minimum evidence thresholds.
- Insufficient data returns “not enough data,” not “weak.”
- Expose readiness component inputs/weights and version formula changes.

## API conventions
- Keep current unversioned routes operational during compatibility transition.
- Introduce /api/v1/ for new contract when versioning is adopted.
- Use plural resources, standard HTTP semantics and consistent error shapes.
- Add pagination/filtering before large histories are exposed.
- Document OpenAPI schemas.
- Never expose answer keys in quiz-taking responses before submission.

Candidate resource groups: profile, academic-sessions, subjects, chapters, topics, exams, questions, quizzes, quiz-attempts, analytics/weakness, analytics/readiness, plans, tasks, revisions, dashboard.

## Suggested code organization

```text
backend/
  config/
  accounts/
  academics/
  exams/
  assessments/
  analytics/
  planner/
  revision/
  notifications/
  tracker/       # existing compatibility app
  manage.py
```

Use a modular monolith, not microservices. Larger apps can split serializers, selectors, services, views and tests by domain.

## Migration and compatibility strategy
1. Take and verify production backup.
2. Add new tables/nullable relations first.
3. Backfill with repeatable data migrations.
4. Validate row counts and ownership mappings.
5. Deploy compatible read behavior.
6. Switch writes only after verification.
7. Remove legacy structures only in a separately reviewed release.
8. Maintain rollback plan; destructive reverse migrations need explicit approval.

No production schema change is part of Phase 1.

## Test architecture
- Model constraints/defaults/deletion/ownership.
- Serializer validation and boundary values.
- API status/permissions/filtering/pagination.
- Service tests for weakness, readiness, planner and revision rules.
- Migration/data-preservation tests.
- Integration: quiz -> performance -> revision -> dashboard.
- Regression: current auth, subjects, entries, dashboard, logout.
- Security: cross-user IDOR, token ownership, throttling.
- CI: Django checks, migration drift, tests, and later lint/type checks.

## Operations
Keep GitHub Pages + Render + Neon initially. Keep secrets in host environment variables. Add structured logs, request IDs, error monitoring, backup verification, readiness/health checks and deployment smoke tests.
