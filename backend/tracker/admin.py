from django.contrib import admin

from .models import (
    Subject,
    StudyEntry,
    AcademicProfile,
    Chapter,
    Topic,
    Exam,
)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")
    search_fields = ("name", "user__username")


@admin.register(StudyEntry)
class StudyEntryAdmin(admin.ModelAdmin):
    list_display = (
        "subject",
        "user",
        "study_date",
        "target_hours",
        "actual_hours",
    )
    list_filter = ("study_date",)
    search_fields = ("subject__name", "user__username")


@admin.register(AcademicProfile)
class AcademicProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "course",
        "branch",
        "academic_session",
        "semester",
        "daily_available_hours",
    )
    list_filter = ("course", "branch", "semester")
    search_fields = ("user__username", "course", "branch")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject",
        "user",
        "order",
        "created_at",
    )
    list_filter = ("subject",)
    search_fields = (
        "title",
        "subject__name",
        "user__username",
    )


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "chapter",
        "user",
        "status",
        "order",
    )
    list_filter = ("status",)
    search_fields = (
        "title",
        "chapter__title",
        "user__username",
    )


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "subject",
        "user",
        "exam_date",
        "priority",
    )
    list_filter = ("priority", "exam_date", "subject")
    search_fields = (
        "title",
        "subject__name",
        "user__username",
    )
    date_hierarchy = "exam_date"