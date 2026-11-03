from decimal import Decimal
from copy import deepcopy
from unittest.mock import patch
from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
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

class OfferListAPITests(APITestCase):
    def setUp(self):
        self.url = "/api/offers/"
        self.business = get_user_model().objects.create_user(
            username="list_business",
            first_name="Ben",
            last_name="Example",
        )
        UserProfile.objects.create(
            user=self.business,
            type=UserProfile.AccountType.BUSINESS,
        )
        self.offer = self.create_offer()
        self.create_packages()

    def create_offer(self):
        return Offer.objects.create(
            user=self.business,
            title="Website development",
            description="A responsive business website.",
        )

    def create_packages(self):
        packages = [
            ("basic", "100.00", 7),
            ("standard", "0.00", 10),
            ("premium", "500.00", 0),
        ]
        for offer_type, price, days in packages:
            OfferDetail.objects.create(
                offer=self.offer, title=offer_type.title(),
                revisions=2, delivery_time_in_days=days,
                price=Decimal(price), features=["Responsive layout"],
                offer_type=offer_type,
            )

    def test_anonymous_user_receives_documented_offer_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(set(data), {"count", "next", "previous", "results"})
        self.assertEqual(data["count"], 1)
        self.assertIsNone(data["next"])
        self.assertIsNone(data["previous"])
        self.assertEqual(len(data["results"]), 1)
        self.assert_offer_data(data["results"][0])

    def assert_offer_data(self, item):
        expected_fields = {
            "id", "user", "title", "image", "description",
            "created_at", "updated_at", "details",
            "min_price", "min_delivery_time", "user_details",
        }
        self.assertEqual(set(item), expected_fields)
        self.assertEqual(item["id"], self.offer.pk)
        self.assertEqual(item["user"], self.business.pk)
        self.assertEqual(item["title"], self.offer.title)
        self.assertEqual(item["description"], self.offer.description)
        self.assertIsNone(item["image"])
        self.assertEqual(item["user_details"], {
            "first_name": "Ben", "last_name": "Example",
            "username": "list_business",
        })

    def test_zero_minimum_values_and_relative_package_links_are_returned(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item = response.json()["results"][0]
        self.assertEqual(item["min_price"], 0)
        self.assertEqual(item["min_delivery_time"], 0)
        expected_details = [
            {"id": detail.pk, "url": f"/offerdetails/{detail.pk}/"}
            for detail in self.offer.details.all()
        ]
        self.assertCountEqual(item["details"], expected_details)

    def test_empty_offer_list_returns_paginated_empty_results(self):
        self.offer.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {
            "count": 0,
            "next": None,
            "previous": None,
            "results": [],
        })

    def create_filter_offer(self, user, title, description, price, days):
        offer = Offer.objects.create(
            user=user, title=title, description=description,
        )
        for package_type in ("basic", "standard", "premium"):
            OfferDetail.objects.create(
                offer=offer, title=package_type,
                revisions=1, delivery_time_in_days=days,
                price=Decimal(price), features=["Development"],
                offer_type=package_type,
            )
        return offer

    def prepare_filter_offers(self):
        other_user = get_user_model().objects.create_user(
            username="other_list_business",
        )
        UserProfile.objects.create(user=other_user, type="business")
        cheap = self.create_filter_offer(
            self.business, "Logo design", "Brand identity.", "80.00", 3,
        )
        expensive = self.create_filter_offer(
            other_user, "Backend service", "Workflow automation.", "200.00", 7,
        )
        return cheap, expensive

    def assert_list_ids(self, params, expected_ids):
        response = self.client.get(self.url, params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], len(expected_ids))
        actual_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(actual_ids, expected_ids)

    def test_filters_select_expected_offers(self):
        cheap, expensive = self.prepare_filter_offers()
        cases = [
            ({"creator_id": expensive.user_id}, [expensive.pk]),
            ({"min_price": "80.00"}, [cheap.pk, expensive.pk]),
            ({"min_price": "200.00"}, [expensive.pk]),
            ({"max_delivery_time": 3}, [self.offer.pk, cheap.pk]),
            ({"max_delivery_time": 0}, [self.offer.pk]),
            ({"min_price": "50.00", "max_delivery_time": 3}, [cheap.pk]),
            ({"creator_id": expensive.user_id, "max_delivery_time": 3}, []),
        ]
        for params, expected_ids in cases:
            with self.subTest(params=params):
                self.assert_list_ids(params, expected_ids)

    def test_search_matches_title_and_description_case_insensitively(self):
        cheap, expensive = self.prepare_filter_offers()
        cases = [
            ({"search": "LOGO"}, [cheap.pk]),
            ({"search": "AUTOMATION"}, [expensive.pk]),
            ({"search": "not-present"}, []),
            ({"search": "website", "min_price": "1.00"}, []),
        ]
        for params, expected_ids in cases:
            with self.subTest(params=params):
                self.assert_list_ids(params, expected_ids)

    def test_offers_can_be_ordered_by_minimum_price(self):
        cheap, expensive = self.prepare_filter_offers()
        self.assert_list_ids(
            {"ordering": "min_price"},
            [self.offer.pk, cheap.pk, expensive.pk],
        )
        self.assert_list_ids(
            {"ordering": "-min_price"},
            [expensive.pk, cheap.pk, self.offer.pk],
        )

    def test_offers_can_be_ordered_by_update_time(self):
        cheap, expensive = self.prepare_filter_offers()
        now = timezone.now()
        Offer.objects.filter(pk=cheap.pk).update(updated_at=now - timedelta(days=2))
        Offer.objects.filter(pk=expensive.pk).update(updated_at=now - timedelta(days=1))
        Offer.objects.filter(pk=self.offer.pk).update(updated_at=now)
        self.assert_list_ids(
            {"ordering": "updated_at"},
            [cheap.pk, expensive.pk, self.offer.pk],
        )
        self.assert_list_ids(
            {"ordering": "-updated_at"},
            [self.offer.pk, expensive.pk, cheap.pk],
        )

    def test_default_pagination_returns_six_offers_then_remaining_offer(self):
        for index in range(6):
            self.create_filter_offer(
                self.business, f"Extra {index}", "Pagination test.", "10.00", 1,
            )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(response.data["results"]), 6)
        self.assertIsNone(response.data["previous"])
        self.assertIsNotNone(response.data["next"])
        second_page = self.client.get(response.data["next"])
        self.assert_pagination_partition(response, second_page, 7)

    def test_page_size_controls_number_of_results(self):
        self.prepare_filter_offers()
        response = self.client.get(self.url, {"page_size": 2})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIsNotNone(response.data["next"])
        second_page = self.client.get(response.data["next"])
        self.assert_pagination_partition(response, second_page, 3)

    def assert_pagination_partition(self, first_page, second_page, total):
        self.assertEqual(second_page.status_code, status.HTTP_200_OK)
        self.assertEqual(second_page.data["count"], total)
        self.assertEqual(len(second_page.data["results"]), 1)
        self.assertIsNone(second_page.data["next"])
        self.assertIsNotNone(second_page.data["previous"])
        first_ids = {item["id"] for item in first_page.data["results"]}
        second_ids = {item["id"] for item in second_page.data["results"]}
        self.assertFalse(first_ids & second_ids)
        self.assertEqual(
            first_ids | second_ids,
            set(Offer.objects.values_list("id", flat=True)),
        )

    def test_invalid_filter_parameters_return_bad_request(self):
        cases = {
            "creator_id": ["abc", "-1", "1.5"],
            "min_price": ["abc", "-0.01", "NaN", "Infinity"],
            "max_delivery_time": ["abc", "-1", "1.5"],
            "ordering": ["unknown", "-password"],
        }
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    response = self.client.get(self.url, {field: value})
                    self.assertEqual(
                        response.status_code, status.HTTP_400_BAD_REQUEST,
                    )
                    self.assertIn(field, response.data)

    def test_empty_frontend_filters_are_ignored(self):
        cheap, expensive = self.prepare_filter_offers()
        params = {
            "creator_id": "",
            "min_price": "",
            "max_delivery_time": "",
            "ordering": "",
            "search": "   ",
            "page_size": "",
        }
        self.assert_list_ids(
            params, [self.offer.pk, cheap.pk, expensive.pk],
        )

    def test_invalid_page_size_returns_bad_request(self):
        for value in ("abc", "0", "-1", "1.5"):
            with self.subTest(page_size=value):
                response = self.client.get(self.url, {"page_size": value})
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn("page_size", response.data)

class OfferRetrieveAPITests(APITestCase):
    def setUp(self):
        self.business = self.create_user("detail_owner", "business")
        self.customer = self.create_user("detail_customer", "customer")
        self.other_business = self.create_user("detail_reader", "business")
        self.offer = Offer.objects.create(
            user=self.business,
            title="Website development",
            description="A responsive business website.",
        )
        self.packages = self.create_packages()
        self.offer_url = f"/api/offers/{self.offer.pk}/"
        self.package_url = f"/api/offerdetails/{self.packages[1].pk}/"
        self.authenticate(self.customer)

    def create_user(self, username, account_type):
        user = get_user_model().objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        return user

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def create_packages(self):
        values = [
            ("basic", "0.00", 7, -1),
            ("standard", "100.50", 0, 2),
            ("premium", "500.00", 3, 5),
        ]
        return [
            OfferDetail.objects.create(
                offer=self.offer,
                title=f"{kind.title()} website",
                offer_type=kind,
                price=Decimal(price),
                delivery_time_in_days=days,
                revisions=revisions,
                features=["Responsive layout", "Contact form"],
            )
            for kind, price, days, revisions in values
        ]

    def assert_offer_fields(self, data):
        self.assertEqual(
            set(data),
            {
                "id", "user", "title", "image", "description",
                "created_at", "updated_at", "details",
                "min_price", "min_delivery_time",
            },
        )
        self.assertEqual(data["id"], self.offer.pk)
        self.assertEqual(data["user"], self.business.pk)
        self.assertEqual(data["title"], self.offer.title)
        self.assertEqual(data["description"], self.offer.description)
        self.assertIsNone(data["image"])
        self.assertEqual(data["min_price"], 0)
        self.assertEqual(data["min_delivery_time"], 0)
        self.assertEqual(
            parse_datetime(data["created_at"]), self.offer.created_at
        )
        self.assertEqual(
            parse_datetime(data["updated_at"]), self.offer.updated_at
        )

    def assert_package_links(self, details):
        expected = [
            {
                "id": package.pk,
                "url": (
                    "http://testserver/api/offerdetails/"
                    f"{package.pk}/"
                ),
            }
            for package in self.packages
        ]
        self.assertCountEqual(details, expected)
        for detail in details:
            response = self.client.get(detail["url"])
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json()["id"], detail["id"])

    def test_customer_can_read_documented_offer_with_absolute_links(self):
        response = self.client.get(self.offer_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assert_offer_fields(data)
        self.assert_package_links(data["details"])

    def test_customer_can_read_documented_package(self):
        response = self.client.get(self.package_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.json(),
            {
                "id": self.packages[1].pk,
                "title": "Standard website",
                "revisions": 2,
                "delivery_time_in_days": 0,
                "price": 100.5,
                "features": ["Responsive layout", "Contact form"],
                "offer_type": "standard",
            },
        )

    def test_owner_and_other_business_can_read_both_details(self):
        for user in (self.business, self.other_business):
            self.authenticate(user)
            for url in (self.offer_url, self.package_url):
                with self.subTest(user=user.username, url=url):
                    response = self.client.get(url)
                    self.assertEqual(
                        response.status_code, status.HTTP_200_OK
                    )

    def test_anonymous_user_cannot_read_details(self):
        self.client.credentials()

        for url in (self.offer_url, self.package_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, status.HTTP_401_UNAUTHORIZED
                )

    def test_invalid_token_cannot_read_details(self):
        self.client.credentials(
            HTTP_AUTHORIZATION="Token invalid-detail-test-token"
        )

        for url in (self.offer_url, self.package_url):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, status.HTTP_401_UNAUTHORIZED
                )

    def test_unknown_offer_and_package_return_not_found(self):
        missing_offer_id = self.offer.pk + 1000
        missing_package_id = max(p.pk for p in self.packages) + 1000
        urls = [
            f"/api/offers/{missing_offer_id}/",
            f"/api/offerdetails/{missing_package_id}/",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, status.HTTP_404_NOT_FOUND
                )

class OfferUpdateDeleteAPITests(APITestCase):
    def setUp(self):
        self.owner = self.create_user("edit_owner", "business")
        self.other = self.create_user("edit_other", "business")
        self.customer = self.create_user("edit_customer", "customer")
        self.offer = self.create_offer(self.owner, "Original offer")
        self.foreign_offer = self.create_offer(self.other, "Foreign offer")
        self.url = f"/api/offers/{self.offer.pk}/"
        self.authenticate(self.owner)
        self.configure_temporary_media()

    def create_user(self, username, account_type):
        user = get_user_model().objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        return user

    def create_offer(self, user, title):
        offer = Offer.objects.create(
            user=user, title=title, description="Original description",
        )
        for package_type in ("basic", "standard", "premium"):
            OfferDetail.objects.create(
                offer=offer,
                title=f"{package_type} package",
                offer_type=package_type,
                revisions=2,
                delivery_time_in_days=5,
                price=Decimal("100.00"),
                features=["Responsive layout"],
            )
        return offer

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def snapshot(self):
        return (
            list(Offer.objects.order_by("pk").values()),
            list(OfferDetail.objects.order_by("pk").values()),
        )

    def send_write_request(self, method):
        if method == "patch":
            return self.client.patch(
                self.url, {"title": "Unauthorized change"}, format="json",
            )
        return self.client.delete(self.url)

    def test_owner_can_update_title_without_changing_packages(self):
        before = list(self.offer.details.order_by("pk").values())
        response = self.client.patch(
            self.url, {"title": "Updated offer"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertEqual(self.offer.title, "Updated offer")
        self.assertEqual(self.offer.description, "Original description")
        self.assertEqual(self.offer.user_id, self.owner.pk)
        self.assertEqual(
            list(self.offer.details.order_by("pk").values()), before,
        )

    def test_owner_can_update_one_package_and_preserve_ids(self):
        before = list(self.offer.details.order_by("pk").values())
        payload = {"details": [{"offer_type": "standard", "price": "125.50"}]}
        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for package in before:
            if package["offer_type"] == "standard":
                package["price"] = Decimal("125.50")
        self.assertEqual(
            list(self.offer.details.order_by("pk").values()), before,
        )
        self.assertEqual(len(response.data["details"]), 3)

    def test_owner_can_delete_offer_and_its_packages(self):
        package_ids = list(self.offer.details.values_list("pk", flat=True))
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Offer.objects.filter(pk=self.offer.pk).exists())
        self.assertFalse(
            OfferDetail.objects.filter(pk__in=package_ids).exists(),
        )
        self.assertTrue(
            Offer.objects.filter(pk=self.foreign_offer.pk).exists(),
        )
        self.assertEqual(self.foreign_offer.details.count(), 3)

    def test_foreign_users_cannot_update_or_delete_offer(self):
        before = self.snapshot()
        for user in (self.other, self.customer):
            self.authenticate(user)
            for method in ("patch", "delete"):
                with self.subTest(user=user.username, method=method):
                    response = self.send_write_request(method)
                    self.assertEqual(
                        response.status_code, status.HTTP_403_FORBIDDEN,
                    )
                    self.assertEqual(self.snapshot(), before)

    def test_anonymous_user_cannot_update_or_delete_offer(self):
        self.client.credentials()
        before = self.snapshot()
        for method in ("patch", "delete"):
            with self.subTest(method=method):
                response = self.send_write_request(method)
                self.assertEqual(
                    response.status_code, status.HTTP_401_UNAUTHORIZED,
                )
                self.assertEqual(self.snapshot(), before)

    def test_invalid_package_prevents_all_offer_changes(self):
        before = self.snapshot()
        payload = {
            "title": "Must not be saved",
            "details": [{"offer_type": "standard", "price": "-0.01"}],
        }
        response = self.client.patch(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.snapshot(), before)

    def configure_temporary_media(self):
        media_directory = TemporaryDirectory()
        self.addCleanup(media_directory.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

    def create_test_image(self):
        content = BytesIO()
        Image.new("RGB", (2, 2), "blue").save(content, format="PNG")
        return SimpleUploadedFile(
            "offer.png", content.getvalue(), content_type="image/png",
        )

    def test_owner_can_upload_image_without_changing_packages(self):
        before = list(self.offer.details.order_by("pk").values())
        response = self.client.patch(
            self.url, {"image": self.create_test_image()}, format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        self.assertTrue(self.offer.image.name)
        self.assertTrue(
            self.offer.image.storage.exists(self.offer.image.name),
        )
        self.assertEqual(self.offer.title, "Original offer")
        self.assertEqual(
            list(self.offer.details.order_by("pk").values()), before,
        )

    def test_invalid_image_prevents_text_changes(self):
        before = self.snapshot()
        invalid_image = SimpleUploadedFile(
            "invalid.png", b"not an image", content_type="image/png",
        )
        response = self.client.patch(
            self.url,
            {"title": "Must not be saved", "image": invalid_image},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.snapshot(), before)

    def test_invalid_package_identifiers_preserve_all_data(self):
        cases = [
            [{"price": "25.00"}],
            [{"offer_type": "unknown", "price": "25.00"}],
            [{"offer_type": "basic"}, {"offer_type": "basic"}],
        ]
        before = self.snapshot()
        for details in cases:
            with self.subTest(details=details):
                response = self.client.patch(
                    self.url, {"details": details}, format="json",
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST,
                )
                self.assertEqual(self.snapshot(), before)

    def ownership_change_payload(self):
        foreign_package = self.foreign_offer.details.get(offer_type="basic")
        return {
            "user": self.other.pk,
            "title": "Allowed title",
            "details": [{
                "offer_type": "basic",
                "id": foreign_package.pk,
                "price": "35.00",
            }],
        }

    def test_client_cannot_change_offer_owner_or_package_id(self):
        package = self.offer.details.get(offer_type="basic")
        foreign_before = list(self.foreign_offer.details.order_by("pk").values())
        response = self.client.patch(
            self.url, self.ownership_change_payload(), format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.offer.refresh_from_db()
        package.refresh_from_db()
        self.assertEqual(self.offer.user_id, self.owner.pk)
        self.assertEqual(self.offer.title, "Allowed title")
        self.assertEqual(package.price, Decimal("35.00"))
        self.assertEqual(self.offer.details.get(offer_type="basic").pk, package.pk)
        self.assertEqual(
            list(self.foreign_offer.details.order_by("pk").values()),
            foreign_before,
        )

    def fail_standard_package_save(self, instance, *args, **kwargs):
        if instance.offer_type == "standard":
            raise RuntimeError("Simulated package save failure")
        return self.original_package_save(instance, *args, **kwargs)

    def test_save_failure_rolls_back_offer_and_previous_package(self):
        before = self.snapshot()
        self.original_package_save = OfferDetail.save
        payload = {
            "title": "Must be rolled back",
            "details": [
                {"offer_type": "basic", "price": "25.00"},
                {"offer_type": "standard", "price": "50.00"},
            ],
        }
        with patch.object(
            OfferDetail, "save", autospec=True,
            side_effect=self.fail_standard_package_save,
        ) as save_package:
            with self.assertRaisesMessage(RuntimeError, "Simulated package"):
                self.client.patch(self.url, payload, format="json")
        self.assertEqual(save_package.call_count, 2)
        self.assertEqual(self.snapshot(), before)

    def test_unknown_offer_cannot_be_updated_or_deleted(self):
        missing_id = Offer.objects.order_by("-pk").first().pk + 1000
        self.url = f"/api/offers/{missing_id}/"
        before = self.snapshot()
        for method in ("patch", "delete"):
            with self.subTest(method=method):
                response = self.send_write_request(method)
                self.assertEqual(
                    response.status_code, status.HTTP_404_NOT_FOUND,
                )
                self.assertEqual(self.snapshot(), before)
