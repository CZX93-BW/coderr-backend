"""Record package terms at booking time for the customer and provider."""

from copy import deepcopy

from .models import Order


def create_order(customer_user, package):
    """Snapshot the package terms and link the customer and provider.

    Args:
        customer_user: Account placing the booking.
        package: Offer tier selected for purchase.

    Returns:
        An in-progress order containing the terms at booking time.
    """
    # Capture the booked terms so later package edits cannot change an order.
    return Order.objects.create(
        customer_user=customer_user,
        business_user=package.offer.user,
        title=package.title,
        revisions=package.revisions,
        delivery_time_in_days=package.delivery_time_in_days,
        price=package.price,
        features=deepcopy(package.features),
        offer_type=package.offer_type,
        status=Order.Status.IN_PROGRESS,
    )
