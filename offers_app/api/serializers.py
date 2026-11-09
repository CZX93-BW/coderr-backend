"""Represent offers and validate nested package data for creation and updates.
"""

from decimal import Decimal

from rest_framework import serializers

from offers_app.models import Offer, OfferDetail
from offers_app.services import create_offer_with_details, update_offer


class OfferDetailSerializer(serializers.ModelSerializer):
    """Represent and validate the terms of one offer package."""

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
        """Select package fields and protect the package ID."""

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
    """Validate an offer and its three tiers for creation."""

    image = serializers.ImageField(required=False, allow_null=True)
    details = OfferDetailSerializer(many=True)

    class Meta:
        """Select offer creation fields and protect the offer ID."""

        model = Offer
        fields = ["id", "title", "image", "description", "details"]
        read_only_fields = ["id"]

    def validate_details(self, details):
        """Require one package of each supported tier for a new offer."""
        package_types = {detail["offer_type"] for detail in details}
        expected_types = set(OfferDetail.OfferType.values)
        if len(details) != 3 or package_types != expected_types:
            raise serializers.ValidationError(
                "Provide exactly one basic, standard and premium package."
            )
        return details

    def create(self, validated_data):
        """Persist the offer and its validated package details together."""
        return create_offer_with_details(validated_data)


class OfferUserSerializer(serializers.Serializer):
    """Expose the provider's name and username in the offer list."""

    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    username = serializers.CharField(read_only=True)


# The API contract uses relative package links in lists and absolute links
# when retrieving a single offer.
class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Return a package ID and relative link for an offer list entry."""

    url = serializers.SerializerMethodField()

    class Meta:
        """Expose the package ID and relative URL as read-only fields."""

        model = OfferDetail
        fields = ["id", "url"]
        read_only_fields = fields

    def get_url(self, obj):
        """Build the relative package path used in offer list responses."""
        return f"/offerdetails/{obj.pk}/"


class OfferListSerializer(serializers.ModelSerializer):
    """Summarize an offer with provider details and package minima."""

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
        """Select read-only fields for the paginated offer summaries."""

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
    """Return an absolute package URL within an individual offer."""

    url = serializers.HyperlinkedIdentityField(
        view_name="offers:offerdetail-detail",
    )

    class Meta:
        """Expose the package ID and absolute URL as read-only fields."""

        model = OfferDetail
        fields = ["id", "url"]
        read_only_fields = fields


class OfferRetrieveSerializer(OfferListSerializer):
    """Represent an individual offer with links to its package tiers."""

    details = OfferRetrieveLinkSerializer(many=True, read_only=True)

    class Meta(OfferListSerializer.Meta):
        """Select the fields included in a single offer response."""

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


class OfferUpdateSerializer(OfferCreateSerializer):
    """Validate changes to an existing offer and its package tiers."""

    def validate_details(self, value):
        """Reject missing, duplicate or unknown tiers in a partial update."""
        package_types = [item.get("offer_type") for item in value]
        if None in package_types:
            raise serializers.ValidationError(
                "Every supplied package must include offer_type.",
            )
        if len(package_types) != len(set(package_types)):
            raise serializers.ValidationError("Duplicate package types.")
        existing_types = set(
            self.instance.details.values_list("offer_type", flat=True),
        )
        if not set(package_types).issubset(existing_types):
            raise serializers.ValidationError("Unknown package type.")
        return value

    def update(self, instance, validated_data):
        """Apply the supplied offer and tier changes atomically."""
        return update_offer(instance, validated_data)
