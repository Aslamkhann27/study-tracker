from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Subject, StudyEntry

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    class Meta:
        model = User
        fields = ("id", "username", "email", "password")
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "name", "created_at")
        read_only_fields = ("id", "created_at")

class StudyEntrySerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source="subject.name", read_only=True)
    class Meta:
        model = StudyEntry
        fields = ("id", "subject", "subject_name", "study_date", "target_hours", "actual_hours", "notes", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
    def validate(self, attrs):
        subject = attrs.get("subject", getattr(self.instance, "subject", None))
        if subject and subject.user_id != self.context["request"].user.id:
            raise serializers.ValidationError({"subject": "You can only use your own subjects."})
        return attrs
