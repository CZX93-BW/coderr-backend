# Check registration responses, role restrictions and transaction rollback.

from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile


class RegistrationAPITests(APITestCase):
    def setUp(self):
        self.url = "/api/registration/"
        self.payload = {
            "username": "new_customer",
            "email": "customer@example.com",
            "password": "TestPassword123!",
            "repeated_password": "TestPassword123!",
            "type": "customer",
        }

    def test_customer_registration_creates_account_profile_and_token(self):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(Token.objects.count(), 1)
        user = get_user_model().objects.get(username=self.payload["username"])
        profile = UserProfile.objects.get(user=user)
        token = Token.objects.get(user=user)
        self.assertEqual(profile.type, "customer")
        self.assert_registration_response(response, user, token)
        self.assert_registered_user(user)

    def test_business_registration_creates_account_profile_and_token(self):
        self.payload["type"] = "business"

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertEqual(Token.objects.count(), 1)
        user = get_user_model().objects.get(username=self.payload["username"])
        profile = UserProfile.objects.get(user=user)
        token = Token.objects.get(user=user)
        self.assertEqual(profile.type, "business")
        self.assert_registration_response(response, user, token)
        self.assert_registered_user(user)

    def test_password_mismatch_creates_no_registration_data(self):
        self.payload["repeated_password"] = "DifferentPassword123!"

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("repeated_password", response.json())
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(UserProfile.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)

    def test_invalid_account_type_creates_no_registration_data(self):
        for account_type in ("admin", "staff", "invalid"):
            with self.subTest(account_type=account_type):
                payload = self.payload.copy()
                payload["type"] = account_type

                self.assert_invalid_registration(payload, "type")

    def test_missing_required_fields_create_no_registration_data(self):
        for field in self.payload:
            with self.subTest(field=field):
                payload = self.payload.copy()
                payload.pop(field)

                self.assert_invalid_registration(payload, field)

    def test_empty_required_fields_create_no_registration_data(self):
        for field in self.payload:
            for value in ("", None):
                with self.subTest(field=field, value=value):
                    payload = self.payload.copy()
                    payload[field] = value

                    self.assert_invalid_registration(payload, field)

    def test_invalid_email_creates_no_registration_data(self):
        payload = self.payload.copy()
        payload["email"] = "not-an-email"

        self.assert_invalid_registration(payload, "email")

    def test_duplicate_username_preserves_existing_registration(self):
        original_state = self.register_and_capture_state()
        duplicate_payload = self.build_duplicate_username_payload()

        response = self.client.post(
            self.url, duplicate_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.json())
        self.assertEqual(self.get_registration_state(), original_state)

    def register_and_capture_state(self):
        original_response = self.client.post(
            self.url, self.payload, format="json"
        )
        self.assertEqual(
            original_response.status_code, status.HTTP_201_CREATED
        )
        return self.get_registration_state()

    def build_duplicate_username_payload(self):
        payload = self.payload.copy()
        payload.update(
            email="different@example.com",
            password="DifferentPassword123!",
            repeated_password="DifferentPassword123!",
            type="business",
        )
        return payload

    def get_registration_state(self):
        return {
            "users": list(
                get_user_model().objects.order_by("pk").values()
            ),
            "profiles": list(
                UserProfile.objects.order_by("pk").values()
            ),
            "tokens": list(
                Token.objects.order_by("pk").values()
            ),
        }

    def assert_invalid_registration(self, payload, field):
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(field, response.json())
        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(UserProfile.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)

    def assert_registration_response(self, response, user, token):
        expected = {
            "token": token.key,
            "username": self.payload["username"],
            "email": self.payload["email"],
            "user_id": user.pk,
        }
        self.assertEqual(response.json(), expected)

    def assert_registered_user(self, user):
        self.assertEqual(user.email, self.payload["email"])
        self.assertTrue(user.check_password(self.payload["password"]))
        self.assertNotEqual(user.password, self.payload["password"])
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class RegistrationPermissionTests(APITestCase):
    def test_registration_cannot_grant_staff_or_superuser_privileges(self):
        payload = {
            "username": "privilege_attempt",
            "email": "privilege@example.com",
            "password": "TestPassword123!",
            "repeated_password": "TestPassword123!",
            "type": "customer",
            "is_staff": True,
            "is_superuser": True,
        }

        response = self.client.post(
            "/api/registration/", payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(pk=response.data["user_id"])
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.profile.type, "customer")
        self.assertNotIn("is_staff", response.data)
        self.assertNotIn("is_superuser", response.data)


class RegistrationTransactionTests(APITestCase):
    def setUp(self):
        self.payload = {
            "username": "rollback_customer",
            "email": "rollback@example.com",
            "password": "TestPassword123!",
            "repeated_password": "TestPassword123!",
            "type": "customer",
        }

    def test_profile_creation_failure_rolls_back_registration(self):
        self.assert_registration_is_rolled_back(
            "accounts_app.services.UserProfile.objects.create"
        )

    def test_token_creation_failure_rolls_back_registration(self):
        self.assert_registration_is_rolled_back(
            "accounts_app.services.Token.objects.create"
        )

    def assert_registration_is_rolled_back(self, target):
        with patch(target, side_effect=RuntimeError("Simulated failure")):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    "/api/registration/", self.payload, format="json"
                )

        self.assertEqual(get_user_model().objects.count(), 0)
        self.assertEqual(UserProfile.objects.count(), 0)
        self.assertEqual(Token.objects.count(), 0)
