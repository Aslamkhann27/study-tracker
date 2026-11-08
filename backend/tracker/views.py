import uuid
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Sum
from django.utils import timezone

from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.decorators import (
    api_view,
    permission_classes,
    throttle_classes,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Subject,
    StudyEntry,
    AcademicProfile,
    Chapter,
    Topic,
    Exam,
)

from .serializers import (
    RegisterSerializer,
    SubjectSerializer,
    StudyEntrySerializer,
    AcademicProfileSerializer,
    ChapterSerializer,
    TopicSerializer,
    ExamSerializer,
)
User = get_user_model()


# ==========================================
# USER REGISTRATION
# ==========================================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


# ==========================================
# USER LOGOUT
# ==========================================

class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_value = request.data.get("refresh")

        if not refresh_value:
            return Response(
                {"detail": "Refresh token is required."},
                status=400,
            )

        try:
            refresh = RefreshToken(refresh_value)
        except TokenError:
            return Response(
                {"detail": "Invalid refresh token."},
                status=400,
            )

        if str(refresh.get("user_id")) != str(request.user.pk):
            return Response(
                {
                    "detail": (
                        "Refresh token does not belong to "
                        "the authenticated user."
                    )
                },
                status=403,
            )

        try:
            refresh.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid refresh token."},
                status=400,
            )

        return Response(status=204)


# ==========================================
# SUBJECT MANAGEMENT
# ==========================================

class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ==========================================
# STUDY ENTRY MANAGEMENT
# ==========================================

class StudyEntryViewSet(viewsets.ModelViewSet):
    serializer_class = StudyEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            StudyEntry.objects
            .filter(user=self.request.user)
            .select_related("subject")
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


# ==========================================
# ACADEMIC PROFILE
# ==========================================

class AcademicProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, created = AcademicProfile.objects.get_or_create(
            user=request.user
        )

        serializer = AcademicProfileSerializer(profile)

        return Response(serializer.data)

    def put(self, request):
        profile, created = AcademicProfile.objects.get_or_create(
            user=request.user
        )

        serializer = AcademicProfileSerializer(
            profile,
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def patch(self, request):
        profile, created = AcademicProfile.objects.get_or_create(
            user=request.user
        )

        serializer = AcademicProfileSerializer(
            profile,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


# ==========================================
# CHAPTER MANAGEMENT
# ==========================================

class ChapterViewSet(viewsets.ModelViewSet):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            Chapter.objects
            .filter(user=self.request.user)
            .select_related("subject")
            .prefetch_related("topics")
        )

        # Optional subject filter:
        # /api/chapters/?subject=1
        subject_id = self.request.query_params.get("subject")

        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ==========================================
# TOPIC MANAGEMENT
# ==========================================

class TopicViewSet(viewsets.ModelViewSet):
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = (
            Topic.objects
            .filter(user=self.request.user)
            .select_related("chapter")
        )

        # Optional chapter filter:
        # /api/topics/?chapter=1
        chapter_id = self.request.query_params.get("chapter")

        if chapter_id:
            queryset = queryset.filter(chapter_id=chapter_id)

        # Optional status filter:
        # /api/topics/?status=completed
        topic_status = self.request.query_params.get("status")

        if topic_status:
            queryset = queryset.filter(status=topic_status)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ==========================================
# EXAM MANAGEMENT
# ==========================================

class ExamViewSet(viewsets.ModelViewSet):

    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Exam.objects.filter(
            user=self.request.user
        ).select_related("subject")

        priority = self.request.query_params.get("priority")

        if priority:
            queryset = queryset.filter(priority=priority)

        upcoming = self.request.query_params.get("upcoming")

        if upcoming == "true":
            queryset = queryset.filter(
                exam_date__gte=timezone.localdate()
            )

        elif upcoming == "false":
            queryset = queryset.filter(
                exam_date__lt=timezone.localdate()
            )

        subject_id = self.request.query_params.get("subject")

        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
# ==========================================
# DASHBOARD
# ==========================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    today = timezone.localdate()

    entries = StudyEntry.objects.filter(user=request.user)

    today_totals = entries.filter(
        study_date=today
    ).aggregate(
        studied=Sum("actual_hours"),
        target=Sum("target_hours"),
    )

    totals = entries.aggregate(
        studied=Sum("actual_hours"),
        target=Sum("target_hours"),
    )

    daily = (
        entries.values("study_date")
        .annotate(
            studied=Sum("actual_hours"),
            target=Sum("target_hours"),
        )
        .order_by("-study_date")
    )

    by_date = {
        row["study_date"]: row
        for row in daily
    }

    streak = 0
    cursor = today

    while cursor in by_date:
        row = by_date[cursor]
        target = row["target"] or 0

        if target <= 0 or row["studied"] < target * Decimal("0.8"):
            break

        streak += 1
        cursor -= timedelta(days=1)

    return Response({
        "date": today,
        "streak": streak,

        "today": {
            "target_hours": today_totals["target"] or 0,
            "actual_hours": today_totals["studied"] or 0,
        },

        "all_time": {
            "target_hours": totals["target"] or 0,
            "actual_hours": totals["studied"] or 0,
        },

        "subjects": SubjectSerializer(
            Subject.objects.filter(user=request.user),
            many=True,
        ).data,
    })


# ==========================================
# HEALTH CHECK
# ==========================================

@api_view(["GET", "HEAD"])
@permission_classes([AllowAny])
@throttle_classes([])
def health(request):
    """
    Public health endpoint.
    Verifies database and configured cache connectivity.
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

    except Exception:
        return Response(
            {
                "status": "unhealthy",
                "database": "unavailable",
            },
            status=503,
        )

    probe_key = f"healthcheck:{uuid.uuid4().hex}"

    try:
        cache.set(probe_key, "ok", timeout=10)

        if cache.get(probe_key) != "ok":
            raise RuntimeError(
                "Cache health check round trip failed"
            )

        cache.delete(probe_key)

    except Exception:
        return Response(
            {
                "status": "unhealthy",
                "database": "ok",
                "cache": "unavailable",
            },
            status=503,
        )

    return Response({
        "status": "ok",
        "database": "ok",
        "cache": "ok",
    })