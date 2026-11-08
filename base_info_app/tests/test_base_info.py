# Check public access, empty statistics and aggregates across providers.

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review

User = get_user_model()


class BaseInfoAPITests(APITestCase):
    def create_user(self, username, account_type):
        user = User.objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        return user

    def create_offer(self, business, title):
        return Offer.objects.create(
            user=business,
            title=title,
            description="Statistics test offer.",
        )

    def create_review(self, customer, business, rating):
        return Review.objects.create(
            reviewer=customer,
            business_user=business,
            rating=rating,
            description="Statistics test review.",
        )

    def create_rated_providers(self):
        first = self.create_user("stats_provider_a", "business")
        second = self.create_user("stats_provider_b", "business")
        alice = self.create_user("stats_alice", "customer")
        bob = self.create_user("stats_bob", "customer")
        self.create_review(alice, first, 5)
        self.create_review(bob, first, 4)
        return self.create_review(alice, second, 1)

    def assert_statistics(self, *, reviews, average, businesses, offers):
        response = self.client.get("/api/base-info/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data, {
            "review_count": reviews,
            "average_rating": average,
            "business_profile_count": businesses,
            "offer_count": offers,
        })
        for field in ("review_count", "business_profile_count", "offer_count"):
            self.assertIs(type(data[field]), int)
        self.assertIn(type(data["average_rating"]), (int, float))

    def test_anonymous_user_receives_zero_counts_for_empty_database(self):
        self.assert_statistics(reviews=0, average=0.0, businesses=0, offers=0)

    def test_counts_business_profiles_and_individual_offers(self):
        provider = self.create_user("stats_active", "business")
        self.create_user("stats_without_offers", "business")
        self.create_user("stats_customer", "customer")
        User.objects.create_user(username="stats_without_profile")
        first = self.create_offer(provider, "First offer")
        self.create_offer(provider, "Second offer")
        self.create_offer(provider, "Third offer")
        self.assert_statistics(reviews=0, average=0.0, businesses=2, offers=3)
        first.delete()
        self.assert_statistics(reviews=0, average=0.0, businesses=2, offers=2)

    def test_average_uses_all_reviews_and_rounds_to_one_decimal(self):
        self.create_rated_providers()
        self.assert_statistics(reviews=3, average=3.3, businesses=2, offers=0)

    def test_statistics_follow_review_updates_and_deletions(self):
        review = self.create_rated_providers()
        review.rating = 5
        review.save(update_fields=["rating", "updated_at"])
        self.assert_statistics(reviews=3, average=4.7, businesses=2, offers=0)
        review.delete()
        self.assert_statistics(reviews=2, average=4.5, businesses=2, offers=0)
        Review.objects.all().delete()
        self.assert_statistics(reviews=0, average=0.0, businesses=2, offers=0)
