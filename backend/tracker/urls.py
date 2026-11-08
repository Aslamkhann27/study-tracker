from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    SubjectViewSet,
    StudyEntryViewSet,
    AcademicProfileView,
    ChapterViewSet,
    TopicViewSet,
    ExamViewSet,
    dashboard,
    health,
)

router = DefaultRouter()

router.register("subjects", SubjectViewSet, basename="subject")
router.register("entries", StudyEntryViewSet, basename="entry")
router.register("chapters", ChapterViewSet, basename="chapter")
router.register("topics", TopicViewSet, basename="topic")
router.register("exams", ExamViewSet, basename="exam")

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("dashboard/", dashboard, name="dashboard"),
    path("profile/", AcademicProfileView.as_view(), name="academic-profile"),
    path("", include(router.urls)),
]