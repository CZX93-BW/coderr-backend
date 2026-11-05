from collections.abc import Mapping

from django.shortcuts import get_object_or_404
from rest_framework import serializers

from offers_app.models import OfferDetail
from orders_app.models import Order
from orders_app.services import create_order


class OrderSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = (
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


class OrderCreateSerializer(OrderSerializer):
    offer_detail_id = serializers.IntegerField(
        min_value=1,
        write_only=True,
    )

    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + ("offer_detail_id",)

    def create(self, validated_data):
        package = get_object_or_404(
            OfferDetail.objects.select_related("offer__user"),
            pk=validated_data["offer_detail_id"],
        )
        return create_order(
            customer_user=validated_data["customer_user"],
            package=package,
        )


class OrderStatusSerializer(OrderSerializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)

    class Meta(OrderSerializer.Meta):
        read_only_fields = tuple(
            field
            for field in OrderSerializer.Meta.fields
            if field != "status"
        )

    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            extra_fields = set(data) - {"status"}
            if extra_fields:
                raise serializers.ValidationError({
                    field: ["This field may not be updated."]
                    for field in sorted(extra_fields)
                })
        return super().to_internal_value(data)

    def validate(self, attrs):
        if "status" not in attrs:
            raise serializers.ValidationError({
                "status": ["This field is required."],
            })
        return attrs

    def update(self, instance, validated_data):
        instance.status = validated_data["status"]
        instance.save(update_fields=["status", "updated_at"])
        return instance