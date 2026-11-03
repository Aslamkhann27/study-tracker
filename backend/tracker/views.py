from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import Subject, StudyEntry
from .serializers import RegisterSerializer, SubjectSerializer, StudyEntrySerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

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
def health(request):
    """Public health endpoint that verifies database connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return Response({"status": "unhealthy", "database": "unavailable"}, status=503)
    return Response({"status": "ok", "database": "ok"})
