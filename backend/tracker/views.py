import uuid
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Subject, StudyEntry
from .serializers import RegisterSerializer, SubjectSerializer, StudyEntrySerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_value = request.data.get("refresh")
        if not refresh_value:
            return Response({"detail": "Refresh token is required."}, status=400)

        try:
            refresh = RefreshToken(refresh_value)
        except TokenError:
            return Response({"detail": "Invalid refresh token."}, status=400)

        # A valid token is not sufficient: it must belong to the authenticated
        # caller. Otherwise one user could revoke another user's refresh token.
        if str(refresh.get("user_id")) != str(request.user.pk):
            return Response(
                {"detail": "Refresh token does not belong to the authenticated user."},
                status=403,
            )

        try:
            refresh.blacklist()
        except TokenError:
            return Response({"detail": "Invalid refresh token."}, status=400)
        return Response(status=204)


class SubjectViewSet(viewsets.ModelViewSet):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        return Subject.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class StudyEntryViewSet(viewsets.ModelViewSet):
    serializer_class = StudyEntrySerializer

    def get_queryset(self):
        return StudyEntry.objects.filter(user=self.request.user).select_related("subject")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        serializer.save(user=self.request.user)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    today = timezone.localdate()
    entries = StudyEntry.objects.filter(user=request.user)
    today_totals = entries.filter(study_date=today).aggregate(
        studied=Sum("actual_hours"), target=Sum("target_hours")
    )
    totals = entries.aggregate(studied=Sum("actual_hours"), target=Sum("target_hours"))
    daily = entries.values("study_date").annotate(
        studied=Sum("actual_hours"), target=Sum("target_hours")
    ).order_by("-study_date")
    by_date = {row["study_date"]: row for row in daily}
    streak, cursor = 0, today
    while cursor in by_date:
        row = by_date[cursor]
        target = row["target"] or 0
        if target <= 0 or row["studied"] < target * 0.8:
            break
        streak += 1
        cursor -= timedelta(days=1)
    return Response({
        "date": today,
        "streak": streak,
        "today": {"target_hours": today_totals["target"] or 0, "actual_hours": today_totals["studied"] or 0},
        "all_time": {"target_hours": totals["target"] or 0, "actual_hours": totals["studied"] or 0},
        "subjects": SubjectSerializer(Subject.objects.filter(user=request.user), many=True).data,
    })


@api_view(["GET", "HEAD"])
@permission_classes([AllowAny])
@throttle_classes([])
def health(request):
    """Public health endpoint; verifies database and configured cache connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return Response({"status": "unhealthy", "database": "unavailable"}, status=503)

    # A write/read/delete round trip verifies that the configured cache backend
    # (Redis in production when REDIS_URL is set) is actually reachable.
    probe_key = f"healthcheck:{uuid.uuid4().hex}"
    try:
        cache.set(probe_key, "ok", timeout=10)
        if cache.get(probe_key) != "ok":
            raise RuntimeError("Cache health check round trip failed")
        cache.delete(probe_key)
    except Exception:
        return Response(
            {"status": "unhealthy", "database": "ok", "cache": "unavailable"},
            status=503,
        )

    return Response({"status": "ok", "database": "ok", "cache": "ok"})
