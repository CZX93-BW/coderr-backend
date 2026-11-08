from datetime import datetime

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile


PROFILE_FIELDS = {
    "user",
    "username",
    "first_name",
    "last_name",
    "file",
    "location",
    "tel",
    "description",
    "working_hours",
    "type",
    "email",
    "created_at",
}


class ProfileDetailAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile_customer",
            email="profile@example.com",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            type=UserProfile.AccountType.CUSTOMER,
        )
        self.token = Token.objects.create(user=self.user)
        self.url = f"/api/profile/{self.user.pk}/"

    def test_profile_request_without_token_is_rejected(self):
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_valid_token_allows_profile_access(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.pk)
        self.assertEqual(response.data["type"], self.profile.type)

    def test_unknown_token_is_rejected(self):
        first_character = "0" if self.token.key[0] != "0" else "1"
        invalid_key = first_character + self.token.key[1:]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {invalid_key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_inactive_user_token_is_rejected(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_profile_response_contains_documented_fields(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), PROFILE_FIELDS)

    def test_profile_without_image_returns_null(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("file", response.data)
        self.assertIsNone(response.data["file"])

    def test_profile_returns_linked_user_data(self):
        self.user.first_name = "Bastian"
        self.user.last_name = "Example"
        self.user.save(update_fields=["first_name", "last_name"])
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_values = {
            "user": self.user.pk,
            "username": self.user.username,
            "first_name": "Bastian",
            "last_name": "Example",
            "email": self.user.email,
        }
        for field, expected_value in expected_values.items():
            with self.subTest(field=field):
                self.assertEqual(response.data[field], expected_value)

    def test_profile_created_at_matches_user_date_joined(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        created_at = datetime.fromisoformat(response.data["created_at"])
        self.assertEqual(created_at, self.user.date_joined)

    def test_missing_profile_returns_not_found(self):
        self.profile.delete()
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_customer_can_read_another_users_business_profile(self):
        provider = self.create_business_user()
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(f"/api/profile/{provider.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], provider.pk)
        self.assertEqual(response.data["username"], provider.username)
        self.assertEqual(response.data["type"], "business")

    def create_business_user(self):
        provider = get_user_model().objects.create_user(
            username="profile_provider",
        )
        UserProfile.objects.create(
            user=provider,
            type=UserProfile.AccountType.BUSINESS,
        )
        return provider

    def test_profile_lookup_uses_user_id(self):
        self.profile.delete()
        self.profile = UserProfile.objects.create(
            pk=self.user.pk + 100,
            user=self.user,
            type=UserProfile.AccountType.CUSTOMER,
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.pk)

    def test_profile_returns_saved_profile_texts(self):
        expected_values = {
            "location": "Dortmund",
            "tel": "+49 123 456789",
            "description": "Web development services.",
            "working_hours": "Monday to Friday",
        }
        for field, value in expected_values.items():
            setattr(self.profile, field, value)
        self.profile.save(update_fields=list(expected_values))
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for field, value in expected_values.items():
            with self.subTest(field=field):
                self.assertEqual(response.data[field], value)
