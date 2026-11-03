from django.conf import settings
from django.db import models

class Subject(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subjects")
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name"], name="unique_subject_per_user")]

    def __str__(self):
        return self.name

class StudyEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="study_entries")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="entries")
    study_date = models.DateField()
    target_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notes = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-study_date", "subject__name"]
        constraints = [models.UniqueConstraint(fields=["user", "subject", "study_date"], name="unique_daily_subject_entry")]
        indexes = [models.Index(fields=["user", "study_date"])]

    def __str__(self):
        return f"{self.subject.name} - {self.study_date}"
