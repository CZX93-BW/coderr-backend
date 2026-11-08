from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail
from orders_app.models import Order

User = get_user_model()


ORDER_FIELDS = {
    "id", "customer_user", "business_user", "title", "revisions",
    "delivery_time_in_days", "price", "features", "offer_type",
    "status", "created_at", "updated_at",
}


class OrderCreateAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username="buyer")
        cls.business = User.objects.create_user(username="provider")
        UserProfile.objects.create(user=cls.customer, type="customer")
        UserProfile.objects.create(user=cls.business, type="business")
        cls.customer_token = Token.objects.create(user=cls.customer)
        cls.business_token = Token.objects.create(user=cls.business)
        cls.offer = Offer.objects.create(
            user=cls.business,
            title="Website",
            description="A responsive website.",
        )
        cls.package = cls.create_package()

    @classmethod
    def create_package(cls):
        return OfferDetail.objects.create(
            offer=cls.offer,
            title="Website Basic",
            revisions=-1,
            delivery_time_in_days=3,
            price=Decimal("149.90"),
            features=["Responsive layout", "Contact form"],
            offer_type="basic",
        )

    def authenticate(self, token):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def create_order(self):
        return self.client.post(
            "/api/orders/",
            {"offer_detail_id": self.package.pk},
            format="json",
        )

    def test_customer_can_create_order_from_package(self):
        self.authenticate(self.customer_token)
        response = self.create_order()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(response.data["id"], order.pk)
        self.assertEqual(order.customer_user, self.customer)
        self.assertEqual(order.business_user, self.business)
        self.assertEqual(order.status, "in_progress")
        self.assert_package_snapshot(order)

    def assert_package_snapshot(self, order):
        fields = (
            "title", "revisions", "delivery_time_in_days",
            "price", "features", "offer_type",
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(order, field),
                    getattr(self.package, field),
                )

    def test_business_cannot_create_order(self):
        self.authenticate(self.business_token)
        response = self.create_order()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Order.objects.exists())

    def test_anonymous_user_cannot_create_order(self):
        response = self.create_order()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Order.objects.exists())

    def post_as_customer(self, payload):
        self.authenticate(self.customer_token)
        return self.client.post("/api/orders/", payload, format="json")

    def order_snapshot(self, order):
        fields = (
            "id", "customer_user_id", "business_user_id", "title",
            "revisions", "delivery_time_in_days", "price", "features",
            "offer_type", "status", "created_at", "updated_at",
        )
        return {field: getattr(order, field) for field in fields}

    def test_invalid_package_ids_create_no_orders(self):
        payloads = [
            {},
            {"offer_detail_id": None},
            {"offer_detail_id": ""},
            {"offer_detail_id": "abc"},
            {"offer_detail_id": 0},
            {"offer_detail_id": -1},
            {"offer_detail_id": 1.5},
            {"offer_detail_id": True},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.post_as_customer(payload)
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST,
                )
                self.assertFalse(Order.objects.exists())

    def test_unknown_package_returns_not_found(self):
        missing_id = self.package.pk + 1000
        response = self.post_as_customer({"offer_detail_id": missing_id})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Order.objects.exists())

    def test_client_cannot_override_order_data(self):
        payload = {
            "offer_detail_id": self.package.pk,
            "customer_user": self.business.pk,
            "business_user": self.customer.pk,
            "title": "Manipulated title",
            "price": "0.00",
            "revisions": 999,
            "delivery_time_in_days": 999,
            "features": ["Injected feature"],
            "offer_type": "premium",
            "status": "completed",
        }
        response = self.post_as_customer(payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.get()
        self.assertEqual(order.customer_user, self.customer)
        self.assertEqual(order.business_user, self.business)
        self.assertEqual(order.status, "in_progress")
        self.assert_package_snapshot(order)

    def test_response_contains_documented_fields_and_numeric_price(self):
        response = self.post_as_customer(
            {"offer_detail_id": self.package.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(set(data), ORDER_FIELDS)
        self.assertIsInstance(data["price"], (int, float))
        self.assertEqual(Decimal(str(data["price"])), Decimal("149.90"))
        self.assertEqual(data["customer_user"], self.customer.pk)
        self.assertEqual(data["business_user"], self.business.pk)

    def test_package_changes_do_not_change_existing_order(self):
        response = self.post_as_customer(
            {"offer_detail_id": self.package.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        before = self.order_snapshot(order)
        self.update_original_package()
        order.refresh_from_db()
        self.assertEqual(self.order_snapshot(order), before)

    def update_original_package(self):
        changes = {
            "title": "Changed package",
            "price": Decimal("299.00"),
            "features": ["Different feature"],
            "revisions": 5,
            "delivery_time_in_days": 10,
            "offer_type": "premium",
        }
        for field, value in changes.items():
            setattr(self.package, field, value)
        self.package.save()

    def test_deleting_offer_preserves_existing_order(self):
        response = self.post_as_customer(
            {"offer_detail_id": self.package.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get()
        before = self.order_snapshot(order)
        package_id = self.package.pk
        self.offer.delete()
        self.assertFalse(OfferDetail.objects.filter(pk=package_id).exists())
        order.refresh_from_db()
        self.assertEqual(self.order_snapshot(order), before)
