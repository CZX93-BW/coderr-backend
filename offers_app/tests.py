from decimal import Decimal
from copy import deepcopy
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile

from .models import Offer, OfferDetail


class OfferModelTests(TestCase):
    def setUp(self):
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
        detail = self.create_detail()
        self.offer.refresh_from_db()
        detail.refresh_from_db()
        self.assertEqual(self.offer.user, self.user)
        self.assertEqual(detail.offer, self.offer)
        self.assertEqual(list(self.offer.details.all()), [detail])

    def test_offer_can_have_three_distinct_package_types(self):
        for offer_type in ("basic", "standard", "premium"):
            self.create_detail(offer_type=offer_type)
        package_types = set(
            self.offer.details.values_list("offer_type", flat=True)
        )
        self.assertEqual(package_types, {"basic", "standard", "premium"})
        self.assertEqual(self.offer.details.count(), 3)

    def test_duplicate_package_type_is_rejected(self):
        self.create_detail()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_detail()
        self.assertEqual(self.offer.details.count(), 1)

    def test_deleting_offer_only_deletes_its_details(self):
        own_detail = self.create_detail()
        other_offer = Offer.objects.create(
            user=self.user,
            title="Another website",
            description="An independent offer.",
        )
        other_detail = self.create_detail(offer=other_offer)
        self.offer.delete()
        self.assertFalse(OfferDetail.objects.filter(pk=own_detail.pk).exists())
        self.assertTrue(OfferDetail.objects.filter(pk=other_detail.pk).exists())
        self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())

    def test_zero_price_zero_delivery_and_valid_revisions_are_allowed(self):
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

class OfferCreateAPITests(APITestCase):
    def setUp(self):
        self.url = "/api/offers/"
        self.business = self.create_user("offer_business", "business")
        self.customer = self.create_user("offer_customer", "customer")
        self.payload = {
            "title": "Website development",
            "description": "A professional website.",
            "details": [
                self.package_data("basic"),
                self.package_data("standard"),
                self.package_data("premium"),
            ],
        }

    def create_user(self, username, account_type):
        user = get_user_model().objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        return user

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def package_data(self, offer_type):
        return {
            "title": f"{offer_type.title()} website",
            "revisions": 2,
            "delivery_time_in_days": 7,
            "price": "100.00",
            "features": ["Responsive layout"],
            "offer_type": offer_type,
        }

    def test_business_can_create_offer_with_three_packages(self):
        self.authenticate(self.business)
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Offer.objects.count(), 1)
        offer = Offer.objects.get()
        self.assertEqual(offer.user_id, self.business.pk)
        self.assertEqual(offer.title, self.payload["title"])
        self.assertEqual(offer.details.count(), 3)
        self.assertEqual(
            set(offer.details.values_list("offer_type", flat=True)),
            {"basic", "standard", "premium"},
        )

    def test_customer_cannot_create_offer(self):
        self.authenticate(self.customer)
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(OfferDetail.objects.exists())

    def test_anonymous_user_cannot_create_offer(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(OfferDetail.objects.exists())

    def assert_creation_rejected(self, payload):
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(OfferDetail.objects.exists())

    def test_response_contains_documented_offer_and_package_data(self):
        self.authenticate(self.business)
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(set(data), {"id", "title", "image", "description", "details"})
        self.assertEqual(data["id"], Offer.objects.get().pk)
        self.assertEqual(data["title"], self.payload["title"])
        self.assertEqual(data["description"], self.payload["description"])
        self.assertIsNone(data["image"])
        self.assertEqual(len(data["details"]), 3)
        for detail in data["details"]:
            self.assert_package_response(detail)

    def assert_package_response(self, detail):
        expected = self.package_data(detail["offer_type"])
        self.assertEqual(set(detail), set(expected) | {"id"})
        saved = OfferDetail.objects.get(pk=detail["id"])
        self.assertEqual(saved.offer_id, Offer.objects.get().pk)
        self.assertEqual(saved.offer_type, detail["offer_type"])
        self.assertIsInstance(detail["price"], (int, float))
        self.assertEqual(Decimal(str(detail["price"])), Decimal(expected["price"]))
        for field in expected.keys() - {"price"}:
            self.assertEqual(detail[field], expected[field])

    def test_incomplete_duplicate_and_unknown_package_types_are_rejected(self):
        self.authenticate(self.business)
        cases = [
            [],
            ["basic", "standard"],
            ["basic", "standard", "premium", "basic"],
            ["basic", "basic", "premium"],
            ["basic", "standard", "unknown"],
        ]
        for package_types in cases:
            with self.subTest(package_types=package_types):
                payload = deepcopy(self.payload)
                payload["details"] = [self.package_data(item) for item in package_types]
                self.assert_creation_rejected(payload)

    def test_zero_values_and_numeric_strings_are_accepted(self):
        self.authenticate(self.business)
        self.payload["image"] = None
        for detail, revisions in zip(self.payload["details"], (-1, 0, 100)):
            detail.update(price="0.00", delivery_time_in_days="0", revisions=str(revisions))
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OfferDetail.objects.count(), 3)
        self.assertEqual(
            set(OfferDetail.objects.values_list("price", "delivery_time_in_days", "revisions")),
            {(Decimal("0.00"), 0, value) for value in (-1, 0, 100)},
        )

    def test_invalid_package_numbers_create_no_data(self):
        self.authenticate(self.business)
        cases = [
            ("price", "-0.01"),
            ("delivery_time_in_days", -1),
            ("delivery_time_in_days", 1.5),
            ("revisions", -2),
            ("revisions", 1.5),
        ]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                payload = deepcopy(self.payload)
                payload["details"][1][field] = value
                self.assert_creation_rejected(payload)

    def test_client_cannot_choose_another_offer_owner(self):
        self.authenticate(self.business)
        self.payload["user"] = self.customer.pk
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Offer.objects.get().user_id, self.business.pk)

    def create_first_detail_then_fail(self, **kwargs):
        if OfferDetail.objects.exists():
            raise RuntimeError("Simulated package save failure.")
        detail = OfferDetail(**kwargs)
        detail.save()
        return detail

    def test_package_save_failure_rolls_back_offer_and_previous_package(self):
        self.authenticate(self.business)
        with patch(
            "offers_app.services.OfferDetail.objects.create",
            side_effect=self.create_first_detail_then_fail,
        ) as create_detail:
            with self.assertRaisesMessage(RuntimeError, "Simulated package save failure."):
                self.client.post(self.url, self.payload, format="json")
        self.assertEqual(create_detail.call_count, 2)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(OfferDetail.objects.exists())