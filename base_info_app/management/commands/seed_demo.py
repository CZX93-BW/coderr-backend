# Prepare the frontend guest accounts and their sample offer for local use.

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts_app.models import UserProfile
from accounts_app.services import create_registered_user
from offers_app.models import Offer, OfferDetail

User = get_user_model()

OFFER_TITLE = "Demo: Website für dein Unternehmen"

PACKAGES = (
    ("basic", "Landingpage", 1, 3, 100, ["Eine Seite"]),
    ("standard", "Unternehmenswebsite", 2, 5, 250, ["Drei Seiten"]),
    ("premium", "Website mit Kontaktformular", 3, 7, 500,
     ["Fünf Seiten", "Kontaktformular"]),
)


def get_demo_user(username, password, role):
    """Create a missing guest account or verify the existing account before
    reuse.
    """
    email = f"{username}@coderr-demo.example"
    user = User.objects.filter(username=username).first()
    if user is None:
        return create_registered_user(
            {"username": username, "email": email, "password": password},
            role,
        )
    # A repeat run may reuse a demo account only after verifying its identity.
    validate_demo_user(user, email, password, role)
    return user


def validate_demo_user(user, email, password, role):
    """Reject an existing username whose credentials or privileges differ
    from the demo configuration.

    Args:
        user: Existing account using the configured guest username.
        email: Expected demo email address.
        password: Expected guest password.
        role: Expected marketplace profile type.

    Raises:
        CommandError: The account cannot safely be reused as this guest.
    """
    matches = (
        user.email == email
        and user.is_active
        and not user.is_staff
        and not user.is_superuser
        and user.check_password(password)
        and UserProfile.objects.filter(user=user, type=role).exists()
    )
    if not matches:
        raise CommandError(
            f"Username '{user.username}' conflicts with the demo account."
        )


def seed_offer(business):
    """Create the demo offer and fill in any missing package tiers."""
    offer, _ = Offer.objects.get_or_create(
        user=business,
        title=OFFER_TITLE,
        defaults={
            "description": "Eine Website passend zu deinem Unternehmen.",
        },
    )
    for offer_type, title, revisions, days, price, features in PACKAGES:
        OfferDetail.objects.get_or_create(
            offer=offer,
            offer_type=offer_type,
            defaults={
                "title": title, "revisions": revisions, "price": price,
                "delivery_time_in_days": days, "features": features,
            },
        )


class Command(BaseCommand):
    help = "Create guest accounts and a sample offer for the local frontend."

    @transaction.atomic
    def handle(self, *args, **options):
        """Provision both guest accounts and the sample offer atomically."""
        get_demo_user("andrey", "asdasd", UserProfile.AccountType.CUSTOMER)
        business = get_demo_user(
            "kevin", "asdasd24", UserProfile.AccountType.BUSINESS,
        )
        seed_offer(business)
        self.stdout.write(
            self.style.SUCCESS("Demo accounts and offer are ready."),
        )
