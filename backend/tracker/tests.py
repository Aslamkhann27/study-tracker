from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Subject

class StudyTrackerApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="student", password="StrongPass123!")
        self.client.force_authenticate(self.user)

    def test_subject_create_and_list_is_user_scoped(self):
        response = self.client.post("/api/subjects/", {"name": "DSA"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        other = get_user_model().objects.create_user(username="other", password="StrongPass123!")
        Subject.objects.create(user=other, name="Private")
        listing = self.client.get("/api/subjects/")
        self.assertEqual(len(listing.data), 1)

    def test_entry_create(self):
        subject = Subject.objects.create(user=self.user, name="OS")
        response = self.client.post("/api/entries/", {
            "subject": subject.id,
            "study_date": date.today().isoformat(),
            "target_hours": "2.00",
            "actual_hours": "1.50"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_dashboard_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
