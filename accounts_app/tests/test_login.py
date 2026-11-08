# Check token reuse, missing tokens, inactive accounts and invalid
# credentials.

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile


class LoginAPITests(APITestCase):
    def setUp(self):
        """Prepare accounts login fixtures including password, user, token."""
        self.password = "TestPassword123!"
        self.user = get_user_model().objects.create_user(
            username="login_customer",
            email="login@example.com",
            password=self.password,
        )
        UserProfile.objects.create(user=self.user, type="customer")
        self.token = Token.objects.create(user=self.user)
        self.url = "/api/login/"

    def test_valid_login_returns_existing_token_and_user_data(self):
        """Verify that valid login returns existing token and user data."""
        response = self.client.post(
            self.url, self.build_valid_payload(), format="json"
        )

        self.assert_successful_login(response, self.token.key)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)

    def test_wrong_password_is_rejected_without_changing_tokens(self):
        """Verify that wrong password is rejected without changing tokens."""
        payload = {
            "username": self.user.username,
            "password": "WrongPassword123!",
        }

        self.assert_login_is_rejected(payload)

    def test_unknown_username_is_rejected_without_changing_tokens(self):
        """Verify that unknown username is rejected without changing tokens."""
        payload = {
            "username": "unknown_customer",
            "password": self.password,
        }

        self.assert_login_is_rejected(payload)

    def test_missing_login_fields_are_rejected(self):
        """Verify that missing login fields are rejected."""
        for field in ("username", "password"):
            with self.subTest(field=field):
                payload = self.build_valid_payload()
                payload.pop(field)

                self.assert_login_is_rejected(payload, field)

    def test_empty_login_fields_are_rejected(self):
        """Verify that empty login fields are rejected."""
        for field in ("username", "password"):
            for value in ("", None):
                with self.subTest(field=field, value=value):
                    payload = self.build_valid_payload()
                    payload[field] = value

                    self.assert_login_is_rejected(payload, field)

    def test_inactive_user_cannot_log_in(self):
        """Verify that inactive user cannot log in."""
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        self.assert_login_is_rejected(self.build_valid_payload())

    def test_valid_login_creates_token_when_missing(self):
        """Verify that valid login creates token when missing."""
        self.token.delete()

        response = self.client.post(
            self.url, self.build_valid_payload(), format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Token.objects.filter(user=self.user).count(), 1)
        token = Token.objects.get(user=self.user)
        self.assert_successful_login(response, token.key)

    def build_valid_payload(self):
        """Build valid payload."""
        return {
            "username": self.user.username,
            "password": self.password,
        }

    def assert_successful_login(self, response, token_key):
        """Compare the token and identity fields with the expected account."""
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected = {
            "token": token_key,
            "username": self.user.username,
            "email": self.user.email,
            "user_id": self.user.pk,
        }
        self.assertEqual(response.json(), expected)

    def assert_login_is_rejected(
        self, payload, error_field="non_field_errors"
    ):
        """Check the validation error and verify that stored tokens are
        unchanged.
        """
        original_tokens = list(Token.objects.order_by("pk").values())

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(error_field, response.json())
        self.assertNotIn("token", response.json())
        self.assertEqual(
            list(Token.objects.order_by("pk").values()),
            original_tokens,
        )
