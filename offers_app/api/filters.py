from decimal import Decimal

from django.db.models import Q
from rest_framework import serializers
from rest_framework.filters import BaseFilterBackend


class OfferQuerySerializer(serializers.Serializer):
    creator_id = serializers.IntegerField(required=False, min_value=1)
    page_size = serializers.IntegerField(required=False, min_value=1)
    min_price = serializers.DecimalField(
        required=False,
        max_digits=None,
        decimal_places=None,
        min_value=Decimal("0"),
    )
    max_delivery_time = serializers.IntegerField(
        required=False,
        min_value=0,
    )
    search = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        required=False,
        choices=[
            "min_price",
            "-min_price",
            "updated_at",
            "-updated_at",
        ],
    )


class OfferFilterBackend(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        params = self.get_validated_params(request)
        queryset = self.apply_numeric_filters(queryset, params)
        queryset = self.apply_search(queryset, params.get("search"))
        ordering = params.get("ordering")
        if ordering:
            return queryset.order_by(ordering, "id")
        return queryset

    def get_validated_params(self, request):
        data = {
            key: value
            for key, value in request.query_params.items()
            if value.strip() != ""
        }
        serializer = OfferQuerySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def apply_numeric_filters(self, queryset, params):
        lookups = {
            "creator_id": "user_id",
            "min_price": "min_price__gte",
            "max_delivery_time": "min_delivery_time__lte",
        }
        filters = {
            lookup: params[name]
            for name, lookup in lookups.items()
            if name in params
        }
        return queryset.filter(**filters)

    def apply_search(self, queryset, search):
        if not search:
            return queryset
        return queryset.filter(
            Q(title__icontains=search)
            | Q(description__icontains=search)
        )