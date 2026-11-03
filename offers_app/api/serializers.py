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

class OfferUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]
        read_only_fields = fields

    def get_url(self, obj):
        return f"/offerdetails/{obj.pk}/"


class OfferListSerializer(serializers.ModelSerializer):
    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        coerce_to_string=False,
        read_only=True,
        allow_null=True,
    )
    min_delivery_time = serializers.IntegerField(
        read_only=True,
        allow_null=True,
    )
    user_details = OfferUserSerializer(source="user", read_only=True)

    class Meta:
        model = Offer
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
            "user_details",
        ]
        read_only_fields = fields

class OfferRetrieveLinkSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="offers:offerdetail-detail",
    )

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]
        read_only_fields = fields


class OfferRetrieveSerializer(OfferListSerializer):
    details = OfferRetrieveLinkSerializer(many=True, read_only=True)

    class Meta(OfferListSerializer.Meta):
        fields = [
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
        ]
        read_only_fields = fields