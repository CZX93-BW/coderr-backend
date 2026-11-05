from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Order
from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


User = get_user_model()


class OrderModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username="order_customer")
        cls.business = User.objects.create_user(username="order_business")
        cls.order = Order.objects.create(
            customer_user=cls.customer,
            business_user=cls.business,
            title="Website Basic",
            revisions=-1,
            delivery_time_in_days=3,
            price=Decimal("149.90"),
            features=["Responsive layout", "Contact form"],
            offer_type="basic",
        )

    def test_order_stores_participants_and_package_data(self):
        self.order.refresh_from_db()
        self.assertEqual(self.order.customer_user, self.customer)
        self.assertEqual(self.order.business_user, self.business)
        self.assertEqual(self.order.title, "Website Basic")
        self.assertEqual(self.order.revisions, -1)
        self.assertEqual(self.order.delivery_time_in_days, 3)
        self.assertEqual(self.order.price, Decimal("149.90"))
        self.assertEqual(
            self.order.features, ["Responsive layout", "Contact form"],
        )
        self.assertEqual(self.order.offer_type, "basic")

    def test_new_order_starts_in_progress_with_timestamps(self):
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "in_progress")
        self.assertIsNotNone(self.order.created_at)
        self.assertIsNotNone(self.order.updated_at)

    def test_customer_with_order_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.customer.delete()
        self.assertTrue(User.objects.filter(pk=self.customer.pk).exists())
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_business_with_order_cannot_be_deleted(self):
        with self.assertRaises(ProtectedError):
            self.business.delete()
        self.assertTrue(User.objects.filter(pk=self.business.pk).exists())
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

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
        expected_fields = {
            "id", "customer_user", "business_user", "title", "revisions",
            "delivery_time_in_days", "price", "features", "offer_type",
            "status", "created_at", "updated_at",
        }
        self.assertEqual(set(data), expected_fields)
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
        order.refresh_from_db()
        self.assertEqual(self.order_snapshot(order), before)

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

class OrderListAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = cls.create_user("list_customer", "customer")
        cls.other_customer = cls.create_user("list_other", "customer")
        cls.business = cls.create_user("list_business", "business")
        cls.other_business = cls.create_user("list_provider", "business")
        cls.staff = cls.create_user("list_staff", "customer", is_staff=True)
        cls.first = cls.create_order(cls.customer, cls.business)
        cls.second = cls.create_order(cls.customer, cls.other_business)
        cls.foreign = cls.create_order(
            cls.other_customer, cls.other_business,
        )

    @classmethod
    def create_user(cls, username, account_type, **extra):
        user = User.objects.create_user(username=username, **extra)
        UserProfile.objects.create(user=user, type=account_type)
        Token.objects.create(user=user)
        return user

    @classmethod
    def create_order(cls, customer, business):
        return Order.objects.create(
            customer_user=customer,
            business_user=business,
            title="Stored website package",
            revisions=-1,
            delivery_time_in_days=3,
            price=Decimal("149.90"),
            features=["Responsive layout"],
            offer_type="basic",
        )

    def fetch_orders(self, user):
        token = Token.objects.get(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )
        return self.client.get("/api/orders/")

    def assert_order_ids(self, response, expected_ids):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        actual_ids = [order["id"] for order in response.data]
        self.assertCountEqual(actual_ids, expected_ids)

    def test_customer_only_sees_own_purchases(self):
        response = self.fetch_orders(self.customer)
        self.assert_order_ids(response, [self.first.pk, self.second.pk])
        for order in response.data:
            self.assertEqual(order["customer_user"], self.customer.pk)

    def test_business_only_sees_own_sales(self):
        response = self.fetch_orders(self.business)
        self.assert_order_ids(response, [self.first.pk])
        for order in response.data:
            self.assertEqual(order["business_user"], self.business.pk)

    def test_user_without_orders_receives_empty_list(self):
        newcomer = self.create_user("list_newcomer", "customer")
        response = self.fetch_orders(newcomer)
        self.assert_order_ids(response, [])

    def test_staff_cannot_read_unrelated_orders(self):
        response = self.fetch_orders(self.staff)
        self.assert_order_ids(response, [])

    def test_anonymous_user_cannot_list_orders(self):
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class OrderUpdateDeleteAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = cls.create_user("change_customer", "customer")
        cls.business = cls.create_user("change_business", "business")
        cls.other_business = cls.create_user("change_other", "business")
        cls.staff = cls.create_user("change_staff", "customer", is_staff=True)
        cls.order = cls.create_order(cls.business)
        cls.other_order = cls.create_order(cls.other_business)

    @classmethod
    def create_user(cls, username, account_type, **extra):
        user = User.objects.create_user(username=username, **extra)
        UserProfile.objects.create(user=user, type=account_type)
        Token.objects.create(user=user)
        return user

    @classmethod
    def create_order(cls, business):
        return Order.objects.create(
            customer_user=cls.customer,
            business_user=business,
            title="Booked website",
            revisions=-1,
            delivery_time_in_days=3,
            price=Decimal("149.90"),
            features=["Responsive layout"],
            offer_type="basic",
        )

    def authenticate(self, user):
        token = Token.objects.get(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def order_url(self):
        return f"/api/orders/{self.order.pk}/"

    def stored_order(self):
        return Order.objects.values().get(pk=self.order.pk)

    def test_associated_business_can_change_status(self):
        self.authenticate(self.business)
        before = self.stored_order()
        for value in ("completed", "cancelled", "in_progress"):
            with self.subTest(status=value):
                response = self.client.patch(
                    self.order_url(), {"status": value}, format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["status"], value)
                after = self.stored_order()
                self.assertEqual(after["status"], value)
                for field in before.keys() - {"status", "updated_at"}:
                    self.assertEqual(after[field], before[field])

    def test_customer_foreign_business_and_unrelated_staff_cannot_update(self):
        before = self.stored_order()
        for user in (self.customer, self.other_business, self.staff):
            with self.subTest(user=user.username):
                self.authenticate(user)
                response = self.client.patch(
                    self.order_url(), {"status": "completed"}, format="json",
                )
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(self.stored_order(), before)

    def test_invalid_status_or_extra_fields_preserve_order(self):
        self.authenticate(self.business)
        before = self.stored_order()
        payloads = [
            {"status": "unknown"},
            {"status": ""},
            {"status": None},
            {"status": 1},
            {"status": "completed", "price": "0.00"},
            {"status": "completed", "customer_user": self.staff.pk},
            {"status": "completed", "unexpected": "value"},
        ]
        for payload in payloads:
            with self.subTest(payload=payload):
                response = self.client.patch(
                    self.order_url(), payload, format="json",
                )
                self.assertEqual(
                    response.status_code, status.HTTP_400_BAD_REQUEST,
                )
                self.assertEqual(self.stored_order(), before)

    def test_staff_can_delete_unrelated_order_only(self):
        self.authenticate(self.staff)
        other_before = Order.objects.values().get(pk=self.other_order.pk)
        response = self.client.delete(self.order_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())
        self.assertEqual(
            Order.objects.values().get(pk=self.other_order.pk), other_before,
        )
        self.assertTrue(User.objects.filter(pk=self.customer.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.business.pk).exists())

    def test_non_staff_users_cannot_delete_order(self):
        before = self.stored_order()
        for user in (self.customer, self.business, self.other_business):
            with self.subTest(user=user.username):
                self.authenticate(user)
                response = self.client.delete(self.order_url())
                self.assertEqual(
                    response.status_code, status.HTTP_403_FORBIDDEN,
                )
                self.assertEqual(self.stored_order(), before)

    def test_anonymous_user_cannot_update_or_delete_order(self):
        before = self.stored_order()
        responses = [
            self.client.patch(
                self.order_url(), {"status": "completed"}, format="json",
            ),
            self.client.delete(self.order_url()),
        ]
        for response in responses:
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
            )
        self.assertEqual(self.stored_order(), before)

    def test_authorized_users_receive_not_found_for_unknown_order(self):
        missing_url = f"/api/orders/{self.other_order.pk + 1000}/"
        self.authenticate(self.business)
        response = self.client.patch(
            missing_url, {"status": "completed"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.authenticate(self.staff)
        response = self.client.delete(missing_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Order.objects.count(), 2)