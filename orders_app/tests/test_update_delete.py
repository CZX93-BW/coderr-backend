# Exercise participant and staff permissions for order changes and deletion.

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from orders_app.models import Order

User = get_user_model()


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
