from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# ==========================================
# SUBJECT MODEL
# ==========================================

class Subject(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subjects"
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name"],
                name="unique_subject_per_user"
            )
        ]

    def __str__(self):
        return self.name


# ==========================================
# STUDY ENTRY MODEL
# ==========================================

class StudyEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_entries"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="entries"
    )
    study_date = models.DateField()
    target_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0
    )
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-study_date", "subject__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "subject", "study_date"],
                name="unique_daily_subject_entry"
            )
        ]
        indexes = [
            models.Index(fields=["user", "study_date"])
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.study_date}"


# ==========================================
# ACADEMIC PROFILE MODEL
# ==========================================

class AcademicProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="academic_profile"
    )

    course = models.CharField(max_length=100, blank=True)
    branch = models.CharField(max_length=100, blank=True)
    academic_session = models.CharField(max_length=20, blank=True)

    semester = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ]
    )

    daily_available_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=4.00,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(24)
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - Academic Profile"


# ==========================================
# CHAPTER MODEL
# ==========================================

class Chapter(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chapters"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="chapters"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]

        constraints = [
            models.UniqueConstraint(
                fields=["subject", "title"],
                name="unique_chapter_per_subject"
            )
        ]

        indexes = [
            models.Index(fields=["user", "subject"])
        ]

    def __str__(self):
        return f"{self.subject.name} - {self.title}"


# ==========================================
# TOPIC MODEL
# ==========================================

class Topic(models.Model):

    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        NEEDS_REVISION = "needs_revision", "Needs Revision"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topics"
    )

    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        related_name="topics"
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NOT_STARTED
    )

    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]

        constraints = [
            models.UniqueConstraint(
                fields=["chapter", "title"],
                name="unique_topic_per_chapter"
            )
        ]

        indexes = [
            models.Index(fields=["user", "chapter"]),
            models.Index(fields=["user", "status"])
        ]

    def __str__(self):
        return f"{self.chapter.title} - {self.title}"
    # ==========================================
# EXAM MODEL
# ==========================================

class Exam(models.Model):

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="exams"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="exams"
    )

    title = models.CharField(max_length=200)

    exam_date = models.DateField()

    priority = models.CharField(
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["exam_date", "priority"]

        indexes = [
            models.Index(fields=["user", "exam_date"]),
            models.Index(fields=["user", "priority"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.exam_date}"