from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone

from accounts_app.models import UserProfile
from accounts_app.services import create_registered_user


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    repeated_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )
    type = serializers.ChoiceField(
        choices=UserProfile.AccountType.choices,
        write_only=True,
    )

    class Meta:
        model = get_user_model()
        fields = [
            "username",
            "email",
            "password",
            "repeated_password",
            "type",
        ]
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop("repeated_password")
        account_type = validated_data.pop("type")
        return create_registered_user(validated_data, account_type)


class RegistrationResponseSerializer(serializers.ModelSerializer):
    token = serializers.CharField(
        source="auth_token.key",
        read_only=True,
    )
    user_id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        model = get_user_model()
        fields = ["token", "username", "email", "user_id"]
        read_only_fields = fields


class ProfileDetailSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
    )
    first_name = serializers.CharField(
        source="user.first_name",
        read_only=True,
    )
    last_name = serializers.CharField(
        source="user.last_name",
        read_only=True,
    )
    email = serializers.EmailField(
        source="user.email",
        read_only=True,
    )
    created_at = serializers.DateTimeField(
        source="user.date_joined",
        read_only=True,
    )

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "location",
            "tel",
            "description",
            "working_hours",
            "type",
            "email",
            "created_at",
        ]
        read_only_fields = fields

class ProfileUpdateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        source="user.first_name",
        max_length=150,
        required=False,
        allow_blank=True,
    )
    last_name = serializers.CharField(
        source="user.last_name",
        max_length=150,
        required=False,
        allow_blank=True,
    )
    email = serializers.EmailField(
        source="user.email",
        max_length=254,
        required=False,
        allow_blank=True,
    )
    file = serializers.ImageField(
        required=False,
        allow_null=False,
    )

    class Meta:
        model = UserProfile
        fields = [
            "first_name",
            "last_name",
            "location",
            "tel",
            "description",
            "working_hours",
            "email",
            "file",
        ]

    @transaction.atomic
    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if "file" in validated_data:
            validated_data["uploaded_at"] = timezone.now()
        self.update_user_fields(instance.user, user_data)
        return super().update(instance, validated_data)

    def update_user_fields(self, user, user_data):
        if not user_data:
            return
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save(update_fields=list(user_data))