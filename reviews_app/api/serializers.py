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
        if not UserProfile.objects.filter(
            user=value,
            type="business",
        ).exists():
            raise serializers.ValidationError(
                "Reviews must reference a business user.",
            )
        return value

    def create(self, validated_data):
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
        if not attrs:
            raise serializers.ValidationError(
                "Provide a rating or description to update."
            )
        return attrs

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save(update_fields=[*validated_data, "updated_at"])
        return instance
