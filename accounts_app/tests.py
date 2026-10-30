from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
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

    def test_user_cannot_have_multiple_profiles(self):
        user = get_user_model().objects.create_user(
            username="customer_unique",
            password="TestPassword123!",
        )
        profile = UserProfile.objects.create(user=user, type="customer")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserProfile.objects.create(user=user, type="business")

        profile.refresh_from_db()
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
        self.assertEqual(profile.type, "customer")

    def test_deleting_user_only_deletes_their_profile(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="customer_deleted")
        other_user = user_model.objects.create_user(username="customer_kept")
        profile = UserProfile.objects.create(user=user, type="customer")
        other_profile = UserProfile.objects.create(
            user=other_user,
            type="customer",
        )
        user_id = user.pk

        user.delete()

        self.assertFalse(user_model.objects.filter(pk=user_id).exists())
        self.assertFalse(UserProfile.objects.filter(pk=profile.pk).exists())
        self.assertTrue(user_model.objects.filter(pk=other_user.pk).exists())
        self.assertTrue(
            UserProfile.objects.filter(pk=other_profile.pk).exists()
        )