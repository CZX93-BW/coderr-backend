# Check provider-specific counts for in-progress and completed orders.

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from orders_app.models import Order

User = get_user_model()


class OrderCountAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Prepare shared orders counts fixtures including customer,
        business, other business.
        """
        cls.customer = cls.create_user("count_customer", "customer")
        cls.business = cls.create_user("count_business", "business")
        cls.other_business = cls.create_user("count_other", "business")
        cls.empty_business = cls.create_user("count_empty", "business")
        cls.order = cls.create_order(cls.business, "in_progress")
        cls.create_order(cls.business, "in_progress")
        cls.create_order(cls.business, "completed")
        cls.create_order(cls.business, "cancelled")
        cls.create_order(cls.other_business, "in_progress")
        cls.create_order(cls.other_business, "completed")

    @classmethod
    def create_user(cls, username, account_type):
        """Create a test account with its marketplace role."""
        user = User.objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        Token.objects.create(user=user)
        return user

    @classmethod
    def create_order(cls, business, order_status):
        """Create order."""
        return Order.objects.create(
            customer_user=cls.customer,
            business_user=business,
            title="Counter test package",
            revisions=0,
            delivery_time_in_days=1,
            price=Decimal("10.00"),
            features=["Test feature"],
            offer_type="basic",
            status=order_status,
        )

    def authenticate(self, user):
        """Set the API client token for subsequent requests."""
        token = Token.objects.get(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def counter_urls(self, user_id):
        """Counter urls for the test request."""
        return {
            "order_count": f"/api/order-count/{user_id}/",
            "completed_order_count": (
                f"/api/completed-order-count/{user_id}/"
            ),
        }

    def assert_counts(self, user_id, ongoing, completed):
        """Compare both provider counter endpoints with their expected
        totals.
        """
        expected = {
            "order_count": ongoing,
            "completed_order_count": completed,
        }
        for key, url in self.counter_urls(user_id).items():
            with self.subTest(endpoint=key):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json(), {key: expected[key]})
                self.assertIs(type(response.json()[key]), int)

    def assert_counter_error(self, user_id, expected_status):
        """Check counter error."""
        for key, url in self.counter_urls(user_id).items():
            with self.subTest(endpoint=key):
                response = self.client.get(url)
                self.assertEqual(response.status_code, expected_status)

    def test_authenticated_users_can_read_provider_specific_counts(self):
        """Verify that authenticated users can read provider specific
        counts.
        """
        for user in (self.customer, self.business, self.other_business):
            with self.subTest(user=user.username):
                self.authenticate(user)
                self.assert_counts(self.business.pk, 2, 1)
                self.assert_counts(self.other_business.pk, 1, 1)

    def test_provider_without_orders_returns_integer_zeros(self):
        """Verify that provider without orders returns integer zeros."""
        self.authenticate(self.customer)
        self.assert_counts(self.empty_business.pk, 0, 0)

    def test_unknown_provider_returns_not_found(self):
        """Verify that unknown provider returns not found."""
        self.authenticate(self.customer)
        self.assert_counter_error(
            self.empty_business.pk + 1000,
            status.HTTP_404_NOT_FOUND,
        )

    def test_customer_id_is_not_a_valid_provider(self):
        """Verify that customer id is not a valid provider."""
        self.authenticate(self.customer)
        self.assert_counter_error(
            self.customer.pk,
            status.HTTP_404_NOT_FOUND,
        )

    def test_anonymous_user_cannot_read_counts(self):
        """Verify that anonymous user cannot read counts."""
        self.assert_counter_error(
            self.business.pk,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_invalid_token_cannot_read_counts(self):
        """Verify that invalid token cannot read counts."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {'0' * 40}")
        self.assert_counter_error(
            self.business.pk,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_counts_follow_saved_status_changes(self):
        """Verify that counts follow saved status changes."""
        self.authenticate(self.business)
        response = self.client.patch(
            f"/api/orders/{self.order.pk}/",
            {"status": "completed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assert_counts(self.business.pk, 1, 2)
        self.assert_counts(self.other_business.pk, 1, 1)
