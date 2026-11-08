# Check public listing, filters, ordering and page boundaries.

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


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
        self.set_update_times(cheap, expensive)
        self.assert_list_ids(
            {"ordering": "updated_at"},
            [cheap.pk, expensive.pk, self.offer.pk],
        )
        self.assert_list_ids(
            {"ordering": "-updated_at"},
            [self.offer.pk, expensive.pk, cheap.pk],
        )

    def set_update_times(self, cheap, expensive):
        now = timezone.now()
        Offer.objects.filter(pk=cheap.pk).update(
            updated_at=now - timedelta(days=2),
        )
        Offer.objects.filter(pk=expensive.pk).update(
            updated_at=now - timedelta(days=1),
        )
        Offer.objects.filter(pk=self.offer.pk).update(updated_at=now)

    def test_default_pagination_returns_six_offers_then_remaining_offer(self):
        self.create_six_extra_offers()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 7)
        self.assertEqual(len(response.data["results"]), 6)
        self.assertIsNone(response.data["previous"])
        self.assertIsNotNone(response.data["next"])
        second_page = self.client.get(response.data["next"])
        self.assert_pagination_partition(response, second_page, 7)

    def create_six_extra_offers(self):
        for index in range(6):
            self.create_filter_offer(
                self.business,
                f"Extra {index}",
                "Pagination test.",
                "10.00",
                1,
            )

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
