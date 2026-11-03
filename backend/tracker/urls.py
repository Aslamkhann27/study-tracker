from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import RegisterView, SubjectViewSet, StudyEntryViewSet, dashboard, health

router = DefaultRouter()
router.register("subjects", SubjectViewSet, basename="subject")
router.register("entries", StudyEntryViewSet, basename="entry")

urlpatterns = [
    path("health/", health, name="health"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("dashboard/", dashboard, name="dashboard"),
    path("", include(router.urls)),
]
