from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer, OfferDetail


User = get_user_model()


class SeedDemoTests(APITestCase):
    def assert_guest_login(self, username, password, role):
        response = self.client.post(
            "/api/login/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = User.objects.get(username=username)
        self.assertEqual(response.data["user_id"], user.pk)
        self.assertTrue(response.data["token"])
        self.assertTrue(
            UserProfile.objects.filter(user=user, type=role).exists(),
        )

    def seed_ids(self):
        return {
            model: list(
                model.objects.order_by("pk").values_list("pk", flat=True),
            )
            for model in (User, UserProfile, Offer, OfferDetail)
        }

    def test_first_run_provides_guest_logins_and_bookable_offer(self):
        call_command("seed_demo")
        self.assert_guest_login("andrey", "asdasd", "customer")
        self.assert_guest_login("kevin", "asdasd24", "business")
        offer = Offer.objects.get(user__username="kevin")
        self.assertCountEqual(
            offer.details.values_list("offer_type", flat=True),
            ["basic", "standard", "premium"],
        )

    def test_second_run_preserves_seed_ids_without_duplicates(self):
        call_command("seed_demo")
        first_run = self.seed_ids()
        call_command("seed_demo")
        self.assertEqual(self.seed_ids(), first_run)
