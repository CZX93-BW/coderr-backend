"""Create and update an offer and its tiers within one transaction."""

from django.db import transaction

from .models import Offer, OfferDetail


@transaction.atomic
def create_offer_with_details(validated_data):
    """Save the offer and all supplied tiers as one transaction."""
    details = validated_data.pop("details")
    if validated_data.get("image") is None:
        validated_data["image"] = ""
    offer = Offer.objects.create(**validated_data)
    for detail in details:
        OfferDetail.objects.create(offer=offer, **detail)
    return offer


def update_offer_package(offer, package_data):
    """Update the matching tier in place to preserve its package ID.

    Args:
        offer: Parent offer that owns the tier.
        package_data: Tier identifier and the fields to update.
    """
    changes = package_data.copy()
    package_type = changes.pop("offer_type")
    # Updating the existing tier preserves the package ID used by clients.
    package = offer.details.get(offer_type=package_type)
    for field, value in changes.items():
        setattr(package, field, value)
    if changes:
        package.save(update_fields=list(changes))


# An invalid package update must roll back changes to the whole offer.
@transaction.atomic
def update_offer(offer, validated_data):
    """Commit the offer fields and nested tier changes together.

    Args:
        offer: Persisted offer being edited.
        validated_data: Partial offer fields and optional package changes.

    Returns:
        The updated offer with the original package IDs.
    """
    changes = validated_data.copy()
    packages = changes.pop("details", [])
    if "image" in changes and changes["image"] is None:
        changes["image"] = ""
    for field, value in changes.items():
        setattr(offer, field, value)
    offer.save()
    for package_data in packages:
        update_offer_package(offer, package_data)
    return offer
