# Check tier constraints and the effect of deleting an offer on related
# rows.

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


class OfferModelTests(TestCase):
    def setUp(self):
        """Prepare offers models fixtures including user, offer."""
        self.user = get_user_model().objects.create_user(
            username="offer_business",
        )
        UserProfile.objects.create(
            user=self.user,
            type=UserProfile.AccountType.BUSINESS,
        )
        self.offer = Offer.objects.create(
            user=self.user,
            title="Website development",
            description="A professional website.",
        )

    def create_detail(self, offer_type="basic", offer=None):
        """Create detail."""
        return OfferDetail.objects.create(
            offer=offer if offer is not None else self.offer,
            title="Website package",
            revisions=2,
            delivery_time_in_days=7,
            price=Decimal("100.00"),
            features=["Responsive layout"],
            offer_type=offer_type,
        )

    def test_offer_and_detail_are_linked_to_their_owners(self):
        """Verify that offer and detail are linked to their owners."""
        detail = self.create_detail()
        self.offer.refresh_from_db()
        detail.refresh_from_db()
        self.assertEqual(self.offer.user, self.user)
        self.assertEqual(detail.offer, self.offer)
        self.assertEqual(list(self.offer.details.all()), [detail])

    def test_offer_can_have_three_distinct_package_types(self):
        """Verify that offer can have three distinct package types."""
        for offer_type in ("basic", "standard", "premium"):
            self.create_detail(offer_type=offer_type)
        package_types = set(
            self.offer.details.values_list("offer_type", flat=True)
        )
        self.assertEqual(package_types, {"basic", "standard", "premium"})
        self.assertEqual(self.offer.details.count(), 3)

    def test_duplicate_package_type_is_rejected(self):
        """Verify that duplicate package type is rejected."""
        self.create_detail()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_detail()
        self.assertEqual(self.offer.details.count(), 1)

    def test_deleting_offer_only_deletes_its_details(self):
        """Verify that deleting offer only deletes its details."""
        own_detail = self.create_detail()
        other_detail = self.create_unrelated_detail()
        self.offer.delete()
        self.assertFalse(OfferDetail.objects.filter(pk=own_detail.pk).exists())
        self.assertTrue(
            OfferDetail.objects.filter(pk=other_detail.pk).exists(),
        )
        self.assertTrue(
            get_user_model().objects.filter(pk=self.user.pk).exists(),
        )

    def create_unrelated_detail(self):
        """Create unrelated detail."""
        other_offer = Offer.objects.create(
            user=self.user,
            title="Another website",
            description="An independent offer.",
        )
        return self.create_detail(offer=other_offer)

    def test_zero_price_zero_delivery_and_valid_revisions_are_allowed(self):
        """Verify that zero price zero delivery and valid revisions are
        allowed.
        """
        detail = self.create_detail()
        detail.price = Decimal("0.00")
        detail.delivery_time_in_days = 0
        for revisions in (-1, 0, 100):
            with self.subTest(revisions=revisions):
                detail.revisions = revisions
                detail.full_clean()
                detail.save()
                detail.refresh_from_db()
                self.assertEqual(detail.price, Decimal("0.00"))
                self.assertEqual(detail.delivery_time_in_days, 0)
                self.assertEqual(detail.revisions, revisions)

    def test_values_below_allowed_minimum_are_rejected(self):
        """Verify that values below allowed minimum are rejected."""
        detail = self.create_detail()
        invalid_values = {
            "price": Decimal("-0.01"),
            "delivery_time_in_days": -1,
            "revisions": -2,
        }
        for field, value in invalid_values.items():
            with self.subTest(field=field, value=value):
                detail.refresh_from_db()
                setattr(detail, field, value)
                with self.assertRaises(ValidationError) as error:
                    detail.full_clean()
                self.assertIn(field, error.exception.message_dict)
