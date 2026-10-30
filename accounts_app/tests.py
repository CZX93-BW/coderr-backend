from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import UserProfile


class UserProfileModelTests(TestCase):
    def test_customer_profile_is_linked_to_user(self):
        user = get_user_model().objects.create_user(
            username="customer_a",
            password="TestPassword123!",
        )

        profile = UserProfile.objects.create(
            user=user,
            type="customer",
        )
        profile.refresh_from_db()

        self.assertEqual(profile.user_id, user.pk)
        self.assertEqual(profile.type, "customer")

    def test_new_profile_has_no_upload_timestamp(self):
        user = get_user_model().objects.create_user(
            username="customer_without_image",
            password="TestPassword123!",
        )

        profile = UserProfile.objects.create(
            user=user,
            type="customer",
        )
        profile.refresh_from_db()

        self.assertIsNone(profile.uploaded_at)

    def test_optional_profile_texts_default_to_empty_strings(self):
        user = get_user_model().objects.create_user(
            username="customer_without_details",
            password="TestPassword123!",
        )
        profile = UserProfile.objects.create(
            user=user,
            type="customer",
        )
        profile.refresh_from_db()

        fields = ("location", "tel", "description", "working_hours")
        for field in fields:
            with self.subTest(field=field):
                self.assertEqual(getattr(profile, field), "")