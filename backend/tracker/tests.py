from datetime import date

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Subject, StudyEntry


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

    def test_entry_rejects_negative_hours(self):
        subject = Subject.objects.create(user=self.user, name="OS")
        response = self.client.post("/api/entries/", {
            "subject": subject.id,
            "study_date": date.today().isoformat(),
            "target_hours": "-1.00",
            "actual_hours": "1.50"
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_blacklists_own_refresh_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = str(RefreshToken.for_user(self.user))
        response = self.client.post("/api/auth/logout/", {"refresh": refresh}, format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        refresh_response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": refresh}, format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_rejects_another_users_refresh_token_without_blacklisting_it(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        other = get_user_model().objects.create_user(username="other", password="StrongPass123!")
        refresh_value = str(RefreshToken.for_user(other))
        response = self.client.post(
            "/api/auth/logout/", {"refresh": refresh_value}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The rightful owner can still use the token: the rejected logout did not revoke it.
        refresh_response = self.client.post(
            "/api/auth/token/refresh/", {"refresh": refresh_value}, format="json"
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)

    def test_logout_rejects_missing_or_invalid_refresh_token(self):
        missing = self.client.post("/api/auth/logout/", {}, format="json")
        invalid = self.client.post("/api/auth/logout/", {"refresh": "not-a-jwt"}, format="json")
        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_users_cannot_access_or_use_another_users_data(self):
        other = get_user_model().objects.create_user(username="other", password="StrongPass123!")
        other_subject = Subject.objects.create(user=other, name="Private")
        other_entry = StudyEntry.objects.create(
            user=other,
            subject=other_subject,
            study_date=date.today(),
            target_hours="2.00",
            actual_hours="1.00",
        )

        listing = self.client.get("/api/entries/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(listing.data, [])

        detail = self.client.get(f"/api/entries/{other_entry.id}/")
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)

        create = self.client.post("/api/entries/", {
            "subject": other_subject.id,
            "study_date": date.today().isoformat(),
            "target_hours": "2.00",
            "actual_hours": "1.00",
        }, format="json")
        self.assertEqual(create.status_code, status.HTTP_400_BAD_REQUEST)

    def test_dashboard_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get("/api/dashboard/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ThrottlingTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.client.force_authenticate(user=None)

    def tearDown(self):
        cache.clear()

    def test_anonymous_auth_requests_are_rate_limited(self):
        # Invalid credentials still count as attempts; the 21st request is throttled.
        for _ in range(20):
            response = self.client.post(
                "/api/auth/token/", {"username": "nobody", "password": "wrong"}, format="json"
            )
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        throttled = self.client.post(
            "/api/auth/token/", {"username": "nobody", "password": "wrong"}, format="json"
        )
        self.assertEqual(throttled.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_public_health_endpoint_is_not_blocked_by_auth_throttle(self):
        for _ in range(25):
            response = self.client.get("/api/health/")
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class HealthEndpointTests(APITestCase):
    def test_health_is_public_and_checks_database(self):
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"status": "ok", "database": "ok"})
