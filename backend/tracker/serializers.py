from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import (
    Subject,
    StudyEntry,
    AcademicProfile,
    Chapter,
    Topic,
)
from .models import (
    Subject,
    StudyEntry,
    AcademicProfile,
    Chapter,
    Topic,
    Exam,
)

User = get_user_model()


# ==========================================
# USER REGISTRATION
# ==========================================

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        try:
            validate_password(validated_data["password"])
        except DjangoValidationError as error:
            raise serializers.ValidationError({
                "password": error.messages
            })

        return User.objects.create_user(**validated_data)


# ==========================================
# SUBJECT SERIALIZER
# ==========================================

class SubjectSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subject
        fields = ("id", "name", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Subject name cannot be blank."
            )

        return value


# ==========================================
# STUDY ENTRY SERIALIZER
# ==========================================

class StudyEntrySerializer(serializers.ModelSerializer):

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    class Meta:
        model = StudyEntry
        fields = (
            "id",
            "subject",
            "subject_name",
            "study_date",
            "target_hours",
            "actual_hours",
            "notes",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        subject = attrs.get(
            "subject",
            getattr(self.instance, "subject", None)
        )

        if subject and subject.user_id != self.context["request"].user.id:
            raise serializers.ValidationError({
                "subject": "You can only use your own subjects."
            })

        for field in ("target_hours", "actual_hours"):
            value = attrs.get(field)

            if value is not None and value < 0:
                raise serializers.ValidationError({
                    field: "Hours cannot be negative."
                })

        return attrs


# ==========================================
# ACADEMIC PROFILE SERIALIZER
# ==========================================

class AcademicProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = AcademicProfile

        fields = (
            "id",
            "course",
            "branch",
            "academic_session",
            "semester",
            "daily_available_hours",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )


# ==========================================
# CHAPTER SERIALIZER
# ==========================================

class ChapterSerializer(serializers.ModelSerializer):

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    topic_count = serializers.IntegerField(
        source="topics.count",
        read_only=True
    )

    class Meta:
        model = Chapter

        fields = (
            "id",
            "subject",
            "subject_name",
            "title",
            "description",
            "order",
            "topic_count",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "topic_count",
        )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Chapter title cannot be blank."
            )

        return value

    def validate_subject(self, value):
        request = self.context["request"]

        if value.user_id != request.user.id:
            raise serializers.ValidationError(
                "You can only add chapters to your own subjects."
            )

        return value


# ==========================================
# TOPIC SERIALIZER
# ==========================================

class TopicSerializer(serializers.ModelSerializer):

    chapter_title = serializers.CharField(
        source="chapter.title",
        read_only=True
    )

    class Meta:
        model = Topic

        fields = (
            "id",
            "chapter",
            "chapter_title",
            "title",
            "description",
            "status",
            "order",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Topic title cannot be blank."
            )

        return value

    def validate_chapter(self, value):
        request = self.context["request"]

        if value.user_id != request.user.id:
            raise serializers.ValidationError(
                "You can only add topics to your own chapters."
            )

        return value
# ==========================================
# EXAM SERIALIZER
# ==========================================

class ExamSerializer(serializers.ModelSerializer):

    subject_name = serializers.CharField(
        source="subject.name",
        read_only=True
    )

    class Meta:
        model = Exam

        fields = (
            "id",
            "subject",
            "subject_name",
            "title",
            "exam_date",
            "priority",
            "description",
            "created_at",
            "updated_at",
        )

        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
        )

    def validate_title(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "Exam title cannot be blank."
            )

        return value

    def validate_subject(self, value):
        request = self.context["request"]

        if value.user_id != request.user.id:
            raise serializers.ValidationError(
                "You can only schedule exams for your own subjects."
            )

        return value