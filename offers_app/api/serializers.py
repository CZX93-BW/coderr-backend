from decimal import Decimal

from rest_framework import serializers

from offers_app.models import Offer, OfferDetail
from offers_app.services import create_offer_with_details


class OfferDetailSerializer(serializers.ModelSerializer):
    price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.00"),
        coerce_to_string=False,
    )
    features = serializers.ListField(
        child=serializers.CharField(),
    )

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]
        read_only_fields = ["id"]


class OfferCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)
    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ["id", "title", "image", "description", "details"]
        read_only_fields = ["id"]

    def validate_details(self, details):
        package_types = {detail["offer_type"] for detail in details}
        expected_types = set(OfferDetail.OfferType.values)
        if len(details) != 3 or package_types != expected_types:
            raise serializers.ValidationError(
                "Provide exactly one basic, standard and premium package."
            )
        return details

    def create(self, validated_data):
        return create_offer_with_details(validated_data)