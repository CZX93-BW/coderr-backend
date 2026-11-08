from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


OFFER_DETAIL_FIELDS = {
    "id", "user", "title", "image", "description",
    "created_at", "updated_at", "details",
    "min_price", "min_delivery_time",
}


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
            OFFER_DETAIL_FIELDS,
        )
        self.assert_offer_values(data)
        self.assertEqual(
            parse_datetime(data["created_at"]), self.offer.created_at
        )
        self.assertEqual(
            parse_datetime(data["updated_at"]), self.offer.updated_at
        )

    def assert_offer_values(self, data):
        self.assertEqual(data["id"], self.offer.pk)
        self.assertEqual(data["user"], self.business.pk)
        self.assertEqual(data["title"], self.offer.title)
        self.assertEqual(data["description"], self.offer.description)
        self.assertIsNone(data["image"])
        self.assertEqual(data["min_price"], 0)
        self.assertEqual(data["min_delivery_time"], 0)

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
