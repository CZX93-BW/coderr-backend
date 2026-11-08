from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from orders_app.models import Order


User = get_user_model()


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
