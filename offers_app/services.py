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