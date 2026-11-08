from copy import deepcopy
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


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
        self.assert_created_offer(data)
        self.assertEqual(len(data["details"]), 3)
        for detail in data["details"]:
            self.assert_package_response(detail)

    def assert_created_offer(self, data):
        self.assertEqual(
            set(data), {"id", "title", "image", "description", "details"},
        )
        self.assertEqual(data["id"], Offer.objects.get().pk)
        self.assertEqual(data["title"], self.payload["title"])
        self.assertEqual(data["description"], self.payload["description"])
        self.assertIsNone(data["image"])

    def assert_package_response(self, detail):
        expected = self.package_data(detail["offer_type"])
        self.assertEqual(set(detail), set(expected) | {"id"})
        saved = OfferDetail.objects.get(pk=detail["id"])
        self.assertEqual(saved.offer_id, Offer.objects.get().pk)
        self.assertEqual(saved.offer_type, detail["offer_type"])
        self.assertIsInstance(detail["price"], (int, float))
        self.assertEqual(
            Decimal(str(detail["price"])),
            Decimal(expected["price"]),
        )
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
                payload["details"] = [
                    self.package_data(item) for item in package_types
                ]
                self.assert_creation_rejected(payload)

    def test_zero_values_and_numeric_strings_are_accepted(self):
        self.authenticate(self.business)
        self.prepare_numeric_string_payload()
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(OfferDetail.objects.count(), 3)
        self.assertEqual(
            set(OfferDetail.objects.values_list(
                "price",
                "delivery_time_in_days",
                "revisions",
            )),
            {(Decimal("0.00"), 0, value) for value in (-1, 0, 100)},
        )

    def prepare_numeric_string_payload(self):
        self.payload["image"] = None
        for detail, revisions in zip(self.payload["details"], (-1, 0, 100)):
            detail.update(
                price="0.00",
                delivery_time_in_days="0",
                revisions=str(revisions),
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
            with self.assertRaisesMessage(
                RuntimeError,
                "Simulated package save failure.",
            ):
                self.client.post(self.url, self.payload, format="json")
        self.assertEqual(create_detail.call_count, 2)
        self.assertFalse(Offer.objects.exists())
        self.assertFalse(OfferDetail.objects.exists())
