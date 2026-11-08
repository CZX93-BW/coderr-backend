# Check stored terms, status defaults and protection of linked accounts.

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from orders_app.models import Order

User = get_user_model()


class OrderModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Prepare shared orders models fixtures including customer,
        business, order.
        """
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
        """Verify that order stores participants and package data."""
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
        """Verify that new order starts in progress with timestamps."""
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "in_progress")
        self.assertIsNotNone(self.order.created_at)
        self.assertIsNotNone(self.order.updated_at)

    def test_customer_with_order_cannot_be_deleted(self):
        """Verify that customer with order cannot be deleted."""
        with self.assertRaises(ProtectedError):
            self.customer.delete()
        self.assertTrue(User.objects.filter(pk=self.customer.pk).exists())
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_business_with_order_cannot_be_deleted(self):
        """Verify that business with order cannot be deleted."""
        with self.assertRaises(ProtectedError):
            self.business.delete()
        self.assertTrue(User.objects.filter(pk=self.business.pk).exists())
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())
