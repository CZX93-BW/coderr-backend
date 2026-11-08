# Check authenticated review listing, participant filters and ordering.

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from reviews_app.models import Review

User = get_user_model()


class ReviewListAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = cls.create_user("list_reviewer", "customer")
        cls.other_customer = cls.create_user("list_other", "customer")
        cls.business = cls.create_user("list_provider", "business")
        cls.other_business = cls.create_user("list_provider_b", "business")
        cls.first = cls.create_review(cls.customer, cls.business, 5)
        cls.second = cls.create_review(cls.other_customer, cls.business, 2)
        cls.third = cls.create_review(cls.customer, cls.other_business, 4)

    @classmethod
    def create_user(cls, username, account_type):
        user = User.objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        Token.objects.create(user=user)
        return user

    @classmethod
    def create_review(cls, reviewer, business, rating):
        return Review.objects.create(
            reviewer=reviewer,
            business_user=business,
            rating=rating,
            description=f"Review from {reviewer.username}.",
        )

    def authenticate(self, user):
        token = Token.objects.get(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def assert_review_data(self, data, review):
        self.assertEqual(set(data), {
            "id", "business_user", "reviewer", "rating",
            "description", "created_at", "updated_at",
        })
        self.assertEqual(data["id"], review.pk)
        self.assertEqual(data["business_user"], review.business_user_id)
        self.assertEqual(data["reviewer"], review.reviewer_id)
        self.assertEqual(data["rating"], review.rating)
        self.assertIs(type(data["rating"]), int)
        self.assertEqual(data["description"], review.description)
        self.assertTrue(data["created_at"])
        self.assertTrue(data["updated_at"])

    def test_authenticated_users_can_read_all_reviews(self):
        expected = {
            review.pk: review
            for review in (self.first, self.second, self.third)
        }
        for user in (self.customer, self.business, self.other_business):
            with self.subTest(user=user.username):
                self.assert_user_can_read_reviews(user, expected)

    def assert_user_can_read_reviews(self, user, expected):
        self.authenticate(user)
        response = self.client.get("/api/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        self.assertCountEqual([item["id"] for item in data], expected)
        for item in data:
            self.assert_review_data(item, expected[item["id"]])

    def test_empty_review_list_returns_empty_array(self):
        Review.objects.all().delete()
        self.authenticate(self.customer)
        response = self.client.get("/api/reviews/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])

    def test_anonymous_user_cannot_list_reviews(self):
        response = self.client.get("/api/reviews/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_cannot_list_reviews(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {'0' * 40}")
        response = self.client.get("/api/reviews/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def assert_list_ids(self, params, expected, ordered=False):
        response = self.client.get("/api/reviews/", params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIsInstance(data, list)
        actual = [item["id"] for item in data]
        if ordered:
            self.assertEqual(actual, expected)
        else:
            self.assertCountEqual(actual, expected)

    def test_reviews_can_be_filtered_by_business(self):
        self.authenticate(self.customer)
        self.assert_list_ids(
            {"business_user_id": self.business.pk},
            [self.first.pk, self.second.pk],
        )
        self.assert_list_ids(
            {"business_user_id": self.other_business.pk},
            [self.third.pk],
        )

    def test_reviews_can_be_filtered_by_reviewer(self):
        self.authenticate(self.business)
        self.assert_list_ids(
            {"reviewer_id": self.customer.pk},
            [self.first.pk, self.third.pk],
        )
        self.assert_list_ids(
            {"reviewer_id": self.other_customer.pk},
            [self.second.pk],
        )

    def test_business_and_reviewer_filters_are_combined(self):
        self.authenticate(self.customer)
        self.assert_list_ids(
            {
                "business_user_id": self.business.pk,
                "reviewer_id": self.customer.pk,
            },
            [self.first.pk],
        )

    def test_filters_without_matches_return_empty_array(self):
        self.authenticate(self.customer)
        self.assert_list_ids(
            {
                "business_user_id": self.other_business.pk,
                "reviewer_id": self.other_customer.pk,
            },
            [],
        )
        self.assert_list_ids(
            {"business_user_id": self.other_business.pk + 1000},
            [],
        )

    def test_reviews_can_be_ordered_by_rating(self):
        self.authenticate(self.customer)
        self.assert_list_ids(
            {"ordering": "rating"},
            [self.second.pk, self.third.pk, self.first.pk],
            ordered=True,
        )
        self.assert_list_ids(
            {"ordering": "-rating"},
            [self.first.pk, self.third.pk, self.second.pk],
            ordered=True,
        )

    def set_distinct_update_times(self):
        base = timezone.now() - timedelta(days=1)
        for review, hours in (
            (self.first, 3),
            (self.second, 1),
            (self.third, 2),
        ):
            Review.objects.filter(pk=review.pk).update(
                updated_at=base + timedelta(hours=hours),
            )

    def test_reviews_can_be_ordered_by_update_time(self):
        self.authenticate(self.customer)
        self.set_distinct_update_times()
        self.assert_list_ids(
            {"ordering": "updated_at"},
            [self.second.pk, self.third.pk, self.first.pk],
            ordered=True,
        )
        self.assert_list_ids(
            {"ordering": "-updated_at"},
            [self.first.pk, self.third.pk, self.second.pk],
            ordered=True,
        )

    def test_default_ordering_uses_latest_update_first(self):
        self.authenticate(self.customer)
        self.set_distinct_update_times()
        self.assert_list_ids(
            {},
            [self.first.pk, self.third.pk, self.second.pk],
            ordered=True,
        )

    def test_empty_optional_filters_are_ignored(self):
        self.authenticate(self.customer)
        self.set_distinct_update_times()
        for value in ("", "   "):
            with self.subTest(value=value):
                self.assert_list_ids(
                    {
                        "business_user_id": value,
                        "reviewer_id": value,
                        "ordering": value,
                    },
                    [self.first.pk, self.third.pk, self.second.pk],
                    ordered=True,
                )

    def test_invalid_id_filters_return_bad_request(self):
        self.authenticate(self.customer)
        for field in ("business_user_id", "reviewer_id"):
            for value in ("abc", "0", "-1", "1.5", "true"):
                with self.subTest(field=field, value=value):
                    response = self.client.get(
                        "/api/reviews/", {field: value},
                    )
                    self.assertEqual(
                        response.status_code,
                        status.HTTP_400_BAD_REQUEST,
                    )
                    self.assertIn(field, response.json())

    def test_unsupported_ordering_returns_bad_request(self):
        self.authenticate(self.customer)
        for value in ("unknown", "reviewer__password", "created_at"):
            with self.subTest(ordering=value):
                response = self.client.get(
                    "/api/reviews/", {"ordering": value},
                )
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn("ordering", response.json())
