from django.contrib.auth import get_user_model
from rest_framework import serializers

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