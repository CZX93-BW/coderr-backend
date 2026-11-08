# Check the one-to-one user relationship, profile defaults and deletion.

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from accounts_app.models import UserProfile


class UserProfileModelTests(TestCase):
    def create_customer_profile(self, username):
        """Create customer profile."""
        user = get_user_model().objects.create_user(username=username)
        return UserProfile.objects.create(user=user, type="customer")

    def test_customer_profile_is_linked_to_user(self):
        """Verify that customer profile is linked to user."""
        profile = self.create_customer_profile("customer_a")
        user = get_user_model().objects.get(username="customer_a")

        profile.refresh_from_db()

        self.assertEqual(profile.user_id, user.pk)
        self.assertEqual(profile.type, "customer")

    def test_new_profile_has_no_upload_timestamp(self):
        """Verify that new profile has no upload timestamp."""
        profile = self.create_customer_profile("customer_without_image")

        profile.refresh_from_db()

        self.assertIsNone(profile.uploaded_at)

    def test_optional_profile_texts_default_to_empty_strings(self):
        """Verify that optional profile texts default to empty strings."""
        profile = self.create_customer_profile("customer_without_details")

        profile.refresh_from_db()

        fields = ("location", "tel", "description", "working_hours")
        for field in fields:
            with self.subTest(field=field):
                self.assertEqual(getattr(profile, field), "")

    def test_user_cannot_have_multiple_profiles(self):
        """Verify that user cannot have multiple profiles."""
        profile = self.create_customer_profile("customer_unique")

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                UserProfile.objects.create(
                    user=profile.user,
                    type="business",
                )

        profile.refresh_from_db()
        profiles = UserProfile.objects.filter(user_id=profile.user_id)
        self.assertEqual(profiles.count(), 1)
        self.assertEqual(profile.type, "customer")

    def test_deleting_user_only_deletes_their_profile(self):
        """Verify that deleting user only deletes their profile."""
        profile = self.create_customer_profile("customer_deleted")
        other_profile = self.create_customer_profile("customer_kept")
        user_model = get_user_model()
        user_id = profile.user_id

        profile.user.delete()

        self.assertFalse(user_model.objects.filter(pk=user_id).exists())
        self.assertFalse(UserProfile.objects.filter(pk=profile.pk).exists())
        self.assertTrue(
            user_model.objects.filter(pk=other_profile.user_id).exists()
        )
        self.assertTrue(
            UserProfile.objects.filter(pk=other_profile.pk).exists()
        )
