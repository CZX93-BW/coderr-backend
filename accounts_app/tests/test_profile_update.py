from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from PIL import Image
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile


class ProfileUpdateAPITests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile_owner",
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            type=UserProfile.AccountType.CUSTOMER,
            location="Berlin",
        )
        self.token = Token.objects.create(user=self.user)
        self.url = f"/api/profile/{self.user.pk}/"
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

    def test_owner_can_update_profile_location(self):
        response = self.client.patch(
            self.url,
            {"location": "Dortmund"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location"], "Dortmund")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, "Dortmund")
        self.assertEqual(self.profile.type, "customer")

    def test_other_customer_cannot_update_profile(self):
        other_user = get_user_model().objects.create_user(
            username="other_customer",
        )
        UserProfile.objects.create(
            user=other_user,
            type=UserProfile.AccountType.CUSTOMER,
        )
        other_token = Token.objects.create(user=other_user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {other_token.key}",
        )
        response = self.client.patch(
            self.url, {"location": "Hamburg"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, "Berlin")

    def test_profile_update_without_token_is_rejected(self):
        self.client.credentials()

        response = self.client.patch(
            self.url,
            {"location": "Hamburg"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, "Berlin")

    def test_owner_can_update_optional_profile_texts(self):
        payload = {
            "tel": "+49 123 456789",
            "description": "Web development services.",
            "working_hours": "Monday to Friday",
        }
        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        for field, value in payload.items():
            with self.subTest(field=field):
                self.assertEqual(response.data[field], value)
                self.assertEqual(getattr(self.profile, field), value)
        self.assertEqual(self.profile.location, "Berlin")

    def test_owner_can_update_linked_user_fields(self):
        payload = {
            "first_name": "Bastian",
            "last_name": "Example",
            "email": "updated@example.com",
        }
        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        for field, value in payload.items():
            with self.subTest(field=field):
                self.assertEqual(response.data[field], value)
                self.assertEqual(getattr(self.user, field), value)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, "Berlin")

    def test_invalid_email_prevents_all_profile_changes(self):
        original_email = self.user.email
        payload = {
            "email": "invalid-email",
            "location": "Hamburg",
        }

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.email, original_email)
        self.assertEqual(self.profile.location, "Berlin")

    def test_profile_save_failure_rolls_back_user_changes(self):
        original_email = self.user.email
        payload = {
            "email": "updated@example.com",
            "location": "Hamburg",
        }
        with patch.object(
            UserProfile,
            "save",
            side_effect=RuntimeError("Simulated profile save failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.patch(self.url, payload, format="json")

        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.email, original_email)
        self.assertEqual(self.profile.location, "Berlin")

    def test_profile_update_cannot_grant_privileges(self):
        payload = {
            "location": "Dortmund",
            "type": "business",
            "is_staff": True,
            "is_superuser": True,
        }

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, "Dortmund")
        self.assertEqual(self.profile.type, "customer")
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)

    def test_owner_can_clear_profile_location(self):
        response = self.client.patch(
            self.url,
            {"location": ""},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["location"], "")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, "")

    def test_null_location_is_rejected_without_changes(self):
        response = self.client.patch(
            self.url,
            {"location": None, "first_name": "Changed"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("location", response.data)
        self.profile.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.profile.location, "Berlin")
        self.assertEqual(self.user.first_name, "")

    def test_text_update_preserves_upload_timestamp(self):
        uploaded_at = timezone.now()
        self.profile.uploaded_at = uploaded_at
        self.profile.save(update_fields=["uploaded_at"])

        response = self.client.patch(
            self.url,
            {"location": "Dortmund"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.location, "Dortmund")
        self.assertEqual(self.profile.uploaded_at, uploaded_at)

    def create_test_image(self):
        image_buffer = BytesIO()
        Image.new("RGB", (2, 2), color="blue").save(
            image_buffer,
            format="PNG",
        )
        return SimpleUploadedFile(
            "profile.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )

    def assert_uploaded_image_is_saved(self, response):
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.file.name)
        self.assertTrue(
            self.profile.file.storage.exists(self.profile.file.name),
        )
        self.assertIsNotNone(self.profile.uploaded_at)
        self.assertEqual(
            response.data["file"],
            f"http://testserver{self.profile.file.url}",
        )

    def test_owner_can_upload_profile_image(self):
        with TemporaryDirectory() as media_directory:
            with self.settings(MEDIA_ROOT=media_directory):
                response = self.client.patch(
                    self.url,
                    {"file": self.create_test_image()},
                    format="multipart",
                )

                self.assert_uploaded_image_is_saved(response)

    def test_invalid_image_prevents_profile_changes(self):
        invalid_image = SimpleUploadedFile(
            "invalid.png",
            b"This is not an image.",
            content_type="image/png",
        )
        response = self.client.patch(
            self.url,
            {"file": invalid_image, "location": "Hamburg"},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.file.name)
        self.assertIsNone(self.profile.uploaded_at)
        self.assertEqual(self.profile.location, "Berlin")

    def upload_image_at(self, uploaded_at):
        with patch(
            "accounts_app.api.serializers.timezone.now",
            return_value=uploaded_at,
        ):
            response = self.client.patch(
                self.url,
                {"file": self.create_test_image()},
                format="multipart",
            )
        self.assert_uploaded_image_is_saved(response)
        self.assertEqual(self.profile.uploaded_at, uploaded_at)
        return self.profile.file.name

    def test_owner_can_replace_profile_image(self):
        first_upload_at = timezone.now()
        second_upload_at = first_upload_at + timedelta(minutes=1)
        with TemporaryDirectory() as media_directory:
            with self.settings(MEDIA_ROOT=media_directory):
                first_name = self.upload_image_at(first_upload_at)
                second_name = self.upload_image_at(second_upload_at)

                self.assertNotEqual(first_name, second_name)
                self.assertEqual(self.profile.file.name, second_name)
