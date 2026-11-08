from django.db import transaction

from .models import Offer, OfferDetail


@transaction.atomic
def create_offer_with_details(validated_data):
    details = validated_data.pop("details")
    if validated_data.get("image") is None:
        validated_data["image"] = ""
    offer = Offer.objects.create(**validated_data)
    for detail in details:
        OfferDetail.objects.create(offer=offer, **detail)
    return offer


def update_offer_package(offer, package_data):
    changes = package_data.copy()
    package_type = changes.pop("offer_type")
    package = offer.details.get(offer_type=package_type)
    for field, value in changes.items():
        setattr(package, field, value)
    if changes:
        package.save(update_fields=list(changes))


@transaction.atomic
def update_offer(offer, validated_data):
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
