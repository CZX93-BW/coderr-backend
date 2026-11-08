from copy import deepcopy

from .models import Order


def create_order(customer_user, package):
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
