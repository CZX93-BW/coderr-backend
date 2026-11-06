from rest_framework import serializers
from rest_framework.filters import BaseFilterBackend


class ReviewFilterSerializer(serializers.Serializer):
    business_user_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    reviewer_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    ordering = serializers.ChoiceField(
        choices=(
            "rating",
            "-rating",
            "updated_at",
            "-updated_at",
        ),
        default="-updated_at",
    )


class ReviewFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        params = {
            key: value
            for key, value in request.query_params.items()
            if value.strip()
        }
        serializer = ReviewFilterSerializer(data=params)
        serializer.is_valid(raise_exception=True)
        filters = dict(serializer.validated_data)
        ordering = filters.pop("ordering")
        return queryset.filter(**filters).order_by(ordering, "-id")