"""Map account and profile records to registration, detail and list responses.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts_app.models import UserProfile
from accounts_app.services import create_registered_user


class RegistrationSerializer(serializers.ModelSerializer):
    """Validate credentials and create a user with a marketplace role."""

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
        """Map registration input to the user model."""

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
        """Require the repeated password to match the submitted password."""
        if attrs["password"] != attrs["repeated_password"]:
            raise serializers.ValidationError(
                {"repeated_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """Create a user and role profile from the validated registration
        fields.
        """
        validated_data.pop("repeated_password")
        account_type = validated_data.pop("type")
        return create_registered_user(validated_data, account_type)


class RegistrationResponseSerializer(serializers.ModelSerializer):
    """Return account details and the token issued at registration."""

    token = serializers.CharField(
        source="auth_token.key",
        read_only=True,
    )
    user_id = serializers.IntegerField(source="pk", read_only=True)

    class Meta:
        """Expose read-only account fields for the registration response."""

        model = get_user_model()
        fields = ["token", "username", "email", "user_id"]
        read_only_fields = fields


class ProfileDetailSerializer(serializers.ModelSerializer):
    """Combine user account fields with marketplace profile details."""

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
        """Select read-only fields for the combined account and profile."""

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
    """Update account and profile fields, including the profile image."""

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
        """Select the profile fields accepted for updates."""

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
        """Save profile and user changes together and timestamp a new
        upload.
        """
        # One PATCH may change both the auth user and its profile.
        user_data = validated_data.pop("user", {})
        if "file" in validated_data:
            validated_data["uploaded_at"] = timezone.now()
        self.update_user_fields(instance.user, user_data)
        return super().update(instance, validated_data)

    def update_user_fields(self, user, user_data):
        """Save only the account fields supplied in the profile update."""
        if not user_data:
            return
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save(update_fields=list(user_data))


class CustomerProfileListSerializer(serializers.ModelSerializer):
    """Expose the fields returned by the customer directory."""

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

    class Meta:
        """Select read-only customer directory fields."""

        model = UserProfile
        fields = [
            "user",
            "username",
            "first_name",
            "last_name",
            "file",
            "uploaded_at",
            "type",
        ]
        read_only_fields = fields


class BusinessProfileListSerializer(serializers.ModelSerializer):
    """Expose the fields returned by the provider directory."""

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

    class Meta:
        """Select read-only provider directory fields."""

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
        ]
        read_only_fields = fields
