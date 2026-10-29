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