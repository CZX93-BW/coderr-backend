from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase


from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from .models import Review


User = get_user_model()


class ReviewModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = User.objects.create_user(username="review_customer")
        cls.other_customer = User.objects.create_user(
            username="review_other_customer",
        )
        cls.business = User.objects.create_user(username="review_business")
        cls.other_business = User.objects.create_user(
            username="review_other_business",
        )

    def review_data(self, **overrides):
        data = {
            "business_user": self.business,
            "reviewer": self.customer,
            "rating": 4,
            "description": "Reliable work and clear communication.",
        }
        data.update(overrides)
        return data

    def test_review_stores_participants_and_content(self):
        review = Review.objects.create(**self.review_data())
        review.refresh_from_db()
        self.assertEqual(review.business_user, self.business)
        self.assertEqual(review.reviewer, self.customer)
        self.assertEqual(review.rating, 4)
        self.assertEqual(
            review.description,
            "Reliable work and clear communication.",
        )

    def test_review_receives_timestamps(self):
        review = Review.objects.create(**self.review_data())
        review.refresh_from_db()
        self.assertIsNotNone(review.created_at)
        self.assertIsNotNone(review.updated_at)
        self.assertGreaterEqual(review.updated_at, review.created_at)

    def test_ratings_from_one_to_five_are_allowed(self):
        for rating in range(1, 6):
            with self.subTest(rating=rating):
                review = Review(**self.review_data(rating=rating))
                review.full_clean()
                self.assertEqual(review.rating, rating)

    def test_ratings_outside_allowed_range_are_rejected(self):
        for rating in (-1, 0, 6):
            with self.subTest(rating=rating):
                review = Review(**self.review_data(rating=rating))
                with self.assertRaises(ValidationError) as error:
                    review.full_clean()
                self.assertIn("rating", error.exception.message_dict)

    def test_same_customer_cannot_review_same_business_twice(self):
        Review.objects.create(**self.review_data())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(**self.review_data(rating=5))
        self.assertEqual(Review.objects.count(), 1)

    def test_different_customer_business_pairs_are_allowed(self):
        first = Review.objects.create(**self.review_data())
        second = Review.objects.create(
            **self.review_data(reviewer=self.other_customer),
        )
        third = Review.objects.create(
            **self.review_data(business_user=self.other_business),
        )
        self.assertEqual(Review.objects.count(), 3)
        self.assertEqual(len({first.pk, second.pk, third.pk}), 3)

class ReviewCreateAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.customer = cls.create_user("review_api_customer", "customer")
        cls.business = cls.create_user("review_api_business", "business")

    @classmethod
    def create_user(cls, username, account_type):
        user = User.objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        Token.objects.create(user=user)
        return user

    def authenticate(self, user):
        token = Token.objects.get(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def payload(self):
        return {
            "business_user": self.business.pk,
            "rating": 5,
            "description": "Excellent work and clear communication.",
        }

    def test_customer_can_create_review(self):
        self.authenticate(self.customer)
        response = self.client.post(
            "/api/reviews/", self.payload(), format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get()
        self.assertEqual(review.reviewer, self.customer)
        self.assertEqual(review.business_user, self.business)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.description, self.payload()["description"])
        self.assertEqual(response.data["id"], review.pk)

    def test_business_cannot_create_review(self):
        self.authenticate(self.business)
        response = self.client.post(
            "/api/reviews/", self.payload(), format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Review.objects.exists())

    def test_anonymous_user_cannot_create_review(self):
        response = self.client.post(
            "/api/reviews/", self.payload(), format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Review.objects.exists())

    def post_review(self, **overrides):
        data = self.payload()
        data.update(overrides)
        return self.client.post("/api/reviews/", data, format="json")

    def assert_rejected_without_data(self, data):
        response = self.client.post(
            "/api/reviews/", data, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_duplicate_review_preserves_existing_review(self):
        self.authenticate(self.customer)
        first = self.post_review()
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        before = list(Review.objects.values())
        response = self.post_review(rating=1, description="Changed text.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(Review.objects.values()), before)

    def test_invalid_ratings_create_no_reviews(self):
        self.authenticate(self.customer)
        for rating in (-1, 0, 6, 1.5, "abc", "", None, True):
            with self.subTest(rating=rating):
                data = self.payload()
                data["rating"] = rating
                self.assert_rejected_without_data(data)

    def test_missing_and_empty_required_fields_create_no_reviews(self):
        self.authenticate(self.customer)
        for field in ("business_user", "rating", "description"):
            for mode in ("missing", "null", "blank"):
                with self.subTest(field=field, mode=mode):
                    data = self.payload()
                    if mode == "missing":
                        data.pop(field)
                    else:
                        data[field] = None if mode == "null" else ""
                    self.assert_rejected_without_data(data)

    def test_invalid_business_users_create_no_reviews(self):
        self.authenticate(self.customer)
        no_profile = User.objects.create_user(username="without_profile")
        invalid_ids = (
            self.customer.pk, no_profile.pk, no_profile.pk + 1000,
            0, -1, "abc", True,
        )
        for user_id in invalid_ids:
            with self.subTest(business_user=user_id):
                data = self.payload()
                data["business_user"] = user_id
                self.assert_rejected_without_data(data)

    def test_client_cannot_choose_another_reviewer(self):
        self.authenticate(self.customer)
        response = self.post_review(reviewer=self.business.pk)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get()
        self.assertEqual(review.reviewer, self.customer)
        self.assertEqual(response.data["reviewer"], self.customer.pk)

    def test_response_contains_documented_fields(self):
        self.authenticate(self.customer)
        response = self.post_review()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(set(data), {
            "id", "business_user", "reviewer", "rating",
            "description", "created_at", "updated_at",
        })
        self.assertIs(type(data["rating"]), int)
        self.assertEqual(data["business_user"], self.business.pk)
        self.assertEqual(data["description"], self.payload()["description"])
        self.assertTrue(data["created_at"])
        self.assertTrue(data["updated_at"])

    def test_different_customer_business_pairs_can_create_reviews(self):
        other_customer = self.create_user("second_reviewer", "customer")
        other_business = self.create_user("second_provider", "business")
        self.authenticate(self.customer)
        first = self.post_review()
        second = self.post_review(business_user=other_business.pk)
        self.authenticate(other_customer)
        third = self.post_review()
        for response in (first, second, third):
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 3)

    def test_invalid_token_cannot_create_review(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {'0' * 40}")
        response = self.post_review()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Review.objects.exists())

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

class ReviewUpdateDeleteAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = cls.create_user("edit_author", "customer")
        cls.other = cls.create_user("edit_other", "customer")
        cls.business = cls.create_user("edit_provider", "business")
        cls.review = cls.create_review(cls.author, "Original review.")
        cls.other_review = cls.create_review(cls.other, "Another review.")

    @classmethod
    def create_user(cls, username, account_type):
        user = User.objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        Token.objects.create(user=user)
        return user

    @classmethod
    def create_review(cls, reviewer, description):
        return Review.objects.create(
            reviewer=reviewer,
            business_user=cls.business,
            rating=4,
            description=description,
        )

    def authenticate(self, user):
        token = Token.objects.get(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def review_url(self):
        return f"/api/reviews/{self.review.pk}/"

    def assert_write_denied(self, expected_status):
        url = self.review_url()
        before = list(Review.objects.order_by("pk").values())
        patch = self.client.patch(url, {"rating": 1}, format="json")
        self.assertEqual(patch.status_code, expected_status)
        delete = self.client.delete(url)
        self.assertEqual(delete.status_code, expected_status)
        self.assertEqual(list(Review.objects.order_by("pk").values()), before)

    def test_author_can_update_rating_only(self):
        self.authenticate(self.author)
        response = self.client.patch(
            self.review_url(), {"rating": 1}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 1)
        self.assertEqual(self.review.description, "Original review.")
        self.assertEqual(self.review.reviewer_id, self.author.pk)
        self.assertEqual(self.review.business_user_id, self.business.pk)

    def test_author_can_update_description_only(self):
        self.authenticate(self.author)
        response = self.client.patch(
            self.review_url(), {"description": "Revised text."}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.description, "Revised text.")
        self.assertEqual(self.review.rating, 4)

    def test_author_can_delete_only_the_target_review(self):
        self.authenticate(self.author)
        response = self.client.delete(self.review_url())
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.content, b"")
        self.assertFalse(Review.objects.filter(pk=self.review.pk).exists())
        self.assertTrue(Review.objects.filter(pk=self.other_review.pk).exists())

    def test_other_reviewer_and_provider_cannot_modify_review(self):
        for user in (self.other, self.business):
            with self.subTest(user=user.username):
                self.authenticate(user)
                self.assert_write_denied(status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_cannot_modify_review(self):
        self.assert_write_denied(status.HTTP_401_UNAUTHORIZED)

    def test_invalid_rating_preserves_description_and_rating(self):
        self.authenticate(self.author)
        response = self.client.patch(
            self.review_url(),
            {"rating": 6, "description": "Should not be saved."},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 4)
        self.assertEqual(self.review.description, "Original review.")

    def patch_review(self, payload):
        return self.client.patch(self.review_url(), payload, format="json")

    def stored_review(self):
        return Review.objects.values().get(pk=self.review.pk)

    def test_author_can_set_maximum_rating_but_cannot_reassign_review(self):
        self.authenticate(self.author)
        provider = self.create_user("another_provider", "business")
        response = self.patch_review({
            "rating": 5,
            "reviewer": self.other.pk,
            "business_user": provider.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.reviewer_id, self.author.pk)
        self.assertEqual(self.review.business_user_id, self.business.pk)

    def test_invalid_ratings_preserve_all_stored_fields(self):
        self.authenticate(self.author)
        before = self.stored_review()
        for value in (0, -1, 6, 1.5, True, None, "", "abc"):
            with self.subTest(rating=value):
                response = self.patch_review({
                    "rating": value,
                    "description": "Attempted change.",
                })
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("rating", response.json())
                self.assertEqual(self.stored_review(), before)

    def test_patch_without_editable_fields_returns_bad_request(self):
        self.authenticate(self.author)
        before = self.stored_review()
        for payload in ({}, {"reviewer": self.other.pk}):
            with self.subTest(payload=payload):
                response = self.patch_review(payload)
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(self.stored_review(), before)

    def test_unknown_review_returns_not_found_for_patch_and_delete(self):
        self.authenticate(self.author)
        unknown_id = max(self.review.pk, self.other_review.pk) + 1
        url = f"/api/reviews/{unknown_id}/"
        patch = self.client.patch(url, {"rating": 3}, format="json")
        delete = self.client.delete(url)
        self.assertEqual(patch.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(delete.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Review.objects.count(), 2)