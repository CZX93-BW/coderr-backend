# Validate review targets, handle duplicate reviews and limit editable
# fields.

from rest_framework import serializers

from accounts_app.models import UserProfile
from reviews_app.models import Review


class ReviewCreateSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = (
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "reviewer",
            "created_at",
            "updated_at",
        )
        validators = []

    def validate_business_user(self, value):
        """Verify that the target account has a business profile."""
        if not UserProfile.objects.filter(
            user=value,
            type="business",
        ).exists():
            raise serializers.ValidationError(
                "Reviews must reference a business user.",
            )
        return value

    def create(self, validated_data):
        """Create one review per customer and provider and reject a
        duplicate.

        Raises:
            ValidationError: The customer has already reviewed this provider.
        """
        review, created = Review.objects.get_or_create(
            reviewer=validated_data.pop("reviewer"),
            business_user=validated_data.pop("business_user"),
            defaults=validated_data,
        )
        if not created:
            raise serializers.ValidationError({
                "non_field_errors": [
                    "You have already reviewed this business.",
                ],
            })
        return review


class ReviewUpdateSerializer(serializers.ModelSerializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)

    class Meta:
        model = Review
        fields = (
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "business_user",
            "reviewer",
            "created_at",
            "updated_at",
        )

    def validate(self, attrs):
        """Require at least one writable review field."""
        if not attrs:
            raise serializers.ValidationError(
                "Provide a rating or description to update."
            )
        return attrs

    def update(self, instance, validated_data):
        """Save the supplied review fields and refresh the update timestamp."""
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save(update_fields=[*validated_data, "updated_at"])
        return instance
