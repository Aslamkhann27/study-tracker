from django.contrib import admin
from .models import Subject, StudyEntry

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username")

@admin.register(StudyEntry)
class StudyEntryAdmin(admin.ModelAdmin):
    list_display = ("subject", "user", "study_date", "target_hours", "actual_hours")
    list_filter = ("study_date",)
    search_fields = ("subject__name", "user__username")
