from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache

from rest_framework import status
from rest_framework.test import APITestCase

from .models import (
    Subject,
    StudyEntry,
    AcademicProfile,
    Chapter,
    Topic,
)


# =====================================================
# STUDY TRACKER API TESTS
# =====================================================

class StudyTrackerApiTests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="student",
            password="StrongPass123!"
        )
        self.client.force_authenticate(self.user)

    def test_subject_create_and_list_is_user_scoped(self):
        response = self.client.post(
            "/api/subjects/",
            {"name": "DSA"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        other = get_user_model().objects.create_user(
            username="other",
            password="StrongPass123!"
        )

        Subject.objects.create(user=other, name="Private")

        listing = self.client.get("/api/subjects/")

        self.assertEqual(len(listing.data), 1)

    def test_entry_create(self):
        subject = Subject.objects.create(
            user=self.user,
            name="OS"
        )

        response = self.client.post(
            "/api/entries/",
            {
                "subject": subject.id,
                "study_date": date.today().isoformat(),
                "target_hours": "2.00",
                "actual_hours": "1.50"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_entry_rejects_negative_hours(self):
        subject = Subject.objects.create(
            user=self.user,
            name="OS"
        )

        response = self.client.post(
            "/api/entries/",
            {
                "subject": subject.id,
                "study_date": date.today().isoformat(),
                "target_hours": "-1.00",
                "actual_hours": "1.50"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_logout_blacklists_own_refresh_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = str(RefreshToken.for_user(self.user))

        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh},
            format="json"
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_logout_rejects_another_users_refresh_token_without_blacklisting_it(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        other = get_user_model().objects.create_user(
            username="other",
            password="StrongPass123!"
        )

        refresh_value = str(RefreshToken.for_user(other))

        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh_value},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": refresh_value},
            format="json"
        )

        self.assertEqual(
            refresh_response.status_code,
            status.HTTP_200_OK
        )

    def test_logout_rejects_missing_or_invalid_refresh_token(self):
        missing = self.client.post(
            "/api/auth/logout/",
            {},
            format="json"
        )

        invalid = self.client.post(
            "/api/auth/logout/",
            {"refresh": "not-a-jwt"},
            format="json"
        )

        self.assertEqual(
            missing.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertEqual(
            invalid.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_users_cannot_access_or_use_another_users_data(self):
        other = get_user_model().objects.create_user(
            username="other",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Private"
        )

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

        detail = self.client.get(
            f"/api/entries/{other_entry.id}/"
        )

        self.assertEqual(
            detail.status_code,
            status.HTTP_404_NOT_FOUND
        )

        create = self.client.post(
            "/api/entries/",
            {
                "subject": other_subject.id,
                "study_date": date.today().isoformat(),
                "target_hours": "2.00",
                "actual_hours": "1.00",
            },
            format="json"
        )

        self.assertEqual(
            create.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_dashboard_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get("/api/dashboard/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )


# =====================================================
# ACADEMIC PROFILE API TESTS
# =====================================================

class AcademicProfileTests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="academic_student",
            password="StrongPass123!"
        )

        self.client.force_authenticate(self.user)

        self.profile_url = "/api/profile/"

    def test_profile_requires_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.profile_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED
        )

    def test_get_profile_creates_default_profile(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            AcademicProfile.objects.filter(user=self.user).count(),
            1
        )

        self.assertEqual(
            response.data["daily_available_hours"],
            "4.00"
        )

    def test_get_profile_does_not_create_duplicate_profiles(self):
        self.client.get(self.profile_url)
        self.client.get(self.profile_url)

        self.assertEqual(
            AcademicProfile.objects.filter(user=self.user).count(),
            1
        )

    def test_patch_profile_updates_selected_fields(self):
        response = self.client.patch(
            self.profile_url,
            {
                "course": "B.Tech",
                "branch": "Computer Science",
                "semester": 3,
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["course"], "B.Tech")
        self.assertEqual(response.data["branch"], "Computer Science")
        self.assertEqual(response.data["semester"], 3)

        profile = AcademicProfile.objects.get(user=self.user)

        self.assertEqual(profile.semester, 3)

    def test_put_profile_updates_complete_profile(self):
        response = self.client.put(
            self.profile_url,
            {
                "course": "B.Tech",
                "branch": "CSE",
                "academic_session": "2025-2029",
                "semester": 3,
                "daily_available_hours": "5.00",
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["course"], "B.Tech")
        self.assertEqual(response.data["branch"], "CSE")
        self.assertEqual(
            response.data["academic_session"],
            "2025-2029"
        )
        self.assertEqual(response.data["semester"], 3)
        self.assertEqual(
            response.data["daily_available_hours"],
            "5.00"
        )

    def test_profile_rejects_invalid_semester(self):
        response = self.client.patch(
            self.profile_url,
            {"semester": 13},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_profile_rejects_daily_hours_above_24(self):
        response = self.client.patch(
            self.profile_url,
            {"daily_available_hours": "25.00"},
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_users_have_separate_academic_profiles(self):
        self.client.patch(
            self.profile_url,
            {
                "course": "B.Tech",
                "branch": "CSE",
                "semester": 3,
            },
            format="json"
        )

        other = get_user_model().objects.create_user(
            username="another_student",
            password="StrongPass123!"
        )

        self.client.force_authenticate(other)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["course"], "")
        self.assertIsNone(response.data["semester"])

        self.assertEqual(
            AcademicProfile.objects.filter(user=other).count(),
            1
        )

        self.assertEqual(
            AcademicProfile.objects.get(user=self.user).course,
            "B.Tech"
        )


# =====================================================
# CHAPTER AND TOPIC API TESTS
# =====================================================

class ChapterTopicApiTests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="chapter_student",
            password="StrongPass123!"
        )

        self.client.force_authenticate(self.user)

        self.subject = Subject.objects.create(
            user=self.user,
            name="Data Structures"
        )

        self.chapter_url = "/api/chapters/"
        self.topic_url = "/api/topics/"

    def test_create_chapter(self):
        response = self.client.post(
            self.chapter_url,
            {
                "subject": self.subject.id,
                "title": "Arrays",
                "description": "Array fundamentals",
                "order": 1,
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(response.data["title"], "Arrays")

        self.assertTrue(
            Chapter.objects.filter(
                user=self.user,
                subject=self.subject,
                title="Arrays"
            ).exists()
        )

    def test_list_chapters_is_user_scoped(self):
        Chapter.objects.create(
            user=self.user,
            subject=self.subject,
            title="Arrays"
        )

        other = get_user_model().objects.create_user(
            username="other_chapter_student",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Operating Systems"
        )

        Chapter.objects.create(
            user=other,
            subject=other_subject,
            title="Processes"
        )

        response = self.client.get(self.chapter_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Arrays")

    def test_chapter_subject_filter(self):
        Chapter.objects.create(
            user=self.user,
            subject=self.subject,
            title="Arrays"
        )

        response = self.client.get(
            f"{self.chapter_url}?subject={self.subject.id}"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_chapter_rejects_another_users_subject(self):
        other = get_user_model().objects.create_user(
            username="foreign_student",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Private Subject"
        )

        response = self.client.post(
            self.chapter_url,
            {
                "subject": other_subject.id,
                "title": "Private Chapter"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_create_topic(self):
        chapter = Chapter.objects.create(
            user=self.user,
            subject=self.subject,
            title="Arrays"
        )

        response = self.client.post(
            self.topic_url,
            {
                "chapter": chapter.id,
                "title": "One Dimensional Arrays",
                "status": "not_started",
                "order": 1,
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.assertEqual(
            response.data["title"],
            "One Dimensional Arrays"
        )

    def test_topic_status_update(self):
        chapter = Chapter.objects.create(
            user=self.user,
            subject=self.subject,
            title="Arrays"
        )

        topic = Topic.objects.create(
            user=self.user,
            chapter=chapter,
            title="Array Traversal"
        )

        response = self.client.patch(
            f"{self.topic_url}{topic.id}/",
            {"status": "completed"},
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")

        topic.refresh_from_db()

        self.assertEqual(topic.status, "completed")

    def test_topic_rejects_invalid_status(self):
        chapter = Chapter.objects.create(
            user=self.user,
            subject=self.subject,
            title="Arrays"
        )

        response = self.client.post(
            self.topic_url,
            {
                "chapter": chapter.id,
                "title": "Array Traversal",
                "status": "invalid_status"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_topic_rejects_another_users_chapter(self):
        other = get_user_model().objects.create_user(
            username="another_student",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Private Subject"
        )

        other_chapter = Chapter.objects.create(
            user=other,
            subject=other_subject,
            title="Private Chapter"
        )

        response = self.client.post(
            self.topic_url,
            {
                "chapter": other_chapter.id,
                "title": "Private Topic"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_topic_status_filter(self):
        chapter = Chapter.objects.create(
            user=self.user,
            subject=self.subject,
            title="Arrays"
        )

        Topic.objects.create(
            user=self.user,
            chapter=chapter,
            title="Array Basics",
            status="completed"
        )

        Topic.objects.create(
            user=self.user,
            chapter=chapter,
            title="Array Searching",
            status="not_started"
        )

        response = self.client.get(
            f"{self.topic_url}?status=completed"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["status"], "completed")

    def test_users_cannot_access_another_users_chapter_or_topic(self):
        other = get_user_model().objects.create_user(
            username="private_student",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Private Subject"
        )

        other_chapter = Chapter.objects.create(
            user=other,
            subject=other_subject,
            title="Private Chapter"
        )

        other_topic = Topic.objects.create(
            user=other,
            chapter=other_chapter,
            title="Private Topic"
        )

        chapter_response = self.client.get(
            f"{self.chapter_url}{other_chapter.id}/"
        )

        topic_response = self.client.get(
            f"{self.topic_url}{other_topic.id}/"
        )

        self.assertEqual(
            chapter_response.status_code,
            status.HTTP_404_NOT_FOUND
        )

        self.assertEqual(
            topic_response.status_code,
            status.HTTP_404_NOT_FOUND
        )


# =====================================================
# THROTTLING TESTS
# =====================================================

class ThrottlingTests(APITestCase):

    def setUp(self):
        cache.clear()
        self.client.force_authenticate(user=None)

    def tearDown(self):
        cache.clear()

    def test_anonymous_auth_requests_are_rate_limited(self):
        for _ in range(20):
            response = self.client.post(
                "/api/auth/token/",
                {
                    "username": "nobody",
                    "password": "wrong"
                },
                format="json"
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_401_UNAUTHORIZED
            )

        throttled = self.client.post(
            "/api/auth/token/",
            {
                "username": "nobody",
                "password": "wrong"
            },
            format="json"
        )

        self.assertEqual(
            throttled.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS
        )

    def test_public_health_endpoint_is_not_blocked_by_auth_throttle(self):
        for _ in range(25):
            response = self.client.get("/api/health/")

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK
            )


# =====================================================
# HEALTH ENDPOINT TESTS
# =====================================================

class HealthEndpointTests(APITestCase):

    def test_health_is_public_and_checks_database_and_cache(self):
        response = self.client.get("/api/health/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data,
            {
                "status": "ok",
                "database": "ok",
                "cache": "ok",
            },
        )

    @patch(
        "tracker.views.cache.set",
        side_effect=ConnectionError("cache unavailable")
    )
    def test_health_reports_cache_failure(self, _mock_cache_set):
        response = self.client.get("/api/health/")

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

        self.assertEqual(
            response.data,
            {
                "status": "unhealthy",
                "database": "ok",
                "cache": "unavailable",
            },
        )
# =====================================================
# EXAM MANAGEMENT API TESTS
# =====================================================

class ExamApiTests(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="exam_student",
            password="StrongPass123!"
        )

        self.client.force_authenticate(self.user)

        self.subject = Subject.objects.create(
            user=self.user,
            name="Data Structures"
        )

        self.exam_url = "/api/exams/"

    def test_create_exam(self):
        response = self.client.post(
            self.exam_url,
            {
                "subject": self.subject.id,
                "title": "DSA Mid Term",
                "exam_date": (date.today() + timedelta(days=10)).isoformat(),
                "priority": "high",
                "description": "Arrays and Linked Lists"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "DSA Mid Term")
        self.assertEqual(response.data["priority"], "high")

    def test_list_exams_is_user_scoped(self):
        from .models import Exam

        Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="My Exam",
            exam_date=date.today()
        )

        other = get_user_model().objects.create_user(
            username="other_exam_student",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Operating Systems"
        )

        Exam.objects.create(
            user=other,
            subject=other_subject,
            title="Private Exam",
            exam_date=date.today()
        )

        response = self.client.get(self.exam_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "My Exam")

    def test_exam_rejects_another_users_subject(self):
        other = get_user_model().objects.create_user(
            username="foreign_exam_student",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Private Subject"
        )

        response = self.client.post(
            self.exam_url,
            {
                "subject": other_subject.id,
                "title": "Private Exam",
                "exam_date": date.today().isoformat(),
                "priority": "high"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_exam_rejects_invalid_priority(self):
        response = self.client.post(
            self.exam_url,
            {
                "subject": self.subject.id,
                "title": "Invalid Priority Exam",
                "exam_date": date.today().isoformat(),
                "priority": "urgent"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_filter_exams_by_priority(self):
        from .models import Exam

        Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="High Priority Exam",
            exam_date=date.today(),
            priority="high"
        )

        Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="Low Priority Exam",
            exam_date=date.today(),
            priority="low"
        )

        response = self.client.get(
            f"{self.exam_url}?priority=high"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["priority"], "high")

    def test_filter_upcoming_exams(self):
        from .models import Exam

        Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="Upcoming Exam",
            exam_date=date.today() + timedelta(days=5)
        )

        Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="Past Exam",
            exam_date=date.today() - timedelta(days=5)
        )

        response = self.client.get(
            f"{self.exam_url}?upcoming=true"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Upcoming Exam")

    def test_filter_past_exams(self):
        from .models import Exam

        Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="Upcoming Exam",
            exam_date=date.today() + timedelta(days=5)
        )

        Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="Past Exam",
            exam_date=date.today() - timedelta(days=5)
        )

        response = self.client.get(
            f"{self.exam_url}?upcoming=false"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Past Exam")

    def test_update_exam(self):
        from .models import Exam

        exam = Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="Original Exam",
            exam_date=date.today()
        )

        response = self.client.patch(
            f"{self.exam_url}{exam.id}/",
            {
                "title": "Updated Exam",
                "priority": "high"
            },
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Exam")
        self.assertEqual(response.data["priority"], "high")

    def test_delete_exam(self):
        from .models import Exam

        exam = Exam.objects.create(
            user=self.user,
            subject=self.subject,
            title="Exam To Delete",
            exam_date=date.today()
        )

        response = self.client.delete(
            f"{self.exam_url}{exam.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

        self.assertFalse(
            Exam.objects.filter(id=exam.id).exists()
        )

    def test_user_cannot_access_another_users_exam(self):
        from .models import Exam

        other = get_user_model().objects.create_user(
            username="private_exam_student",
            password="StrongPass123!"
        )

        other_subject = Subject.objects.create(
            user=other,
            name="Private Subject"
        )

        exam = Exam.objects.create(
            user=other,
            subject=other_subject,
            title="Private Exam",
            exam_date=date.today()
        )

        response = self.client.get(
            f"{self.exam_url}{exam.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND
        )