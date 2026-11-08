from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from reviews_app.models import Review

User = get_user_model()


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
        self.assertTrue(
            Review.objects.filter(pk=self.other_review.pk).exists(),
        )

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
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
                self.assertIn("rating", response.json())
                self.assertEqual(self.stored_review(), before)

    def test_patch_without_editable_fields_returns_bad_request(self):
        self.authenticate(self.author)
        before = self.stored_review()
        for payload in ({}, {"reviewer": self.other.pk}):
            with self.subTest(payload=payload):
                response = self.patch_review(payload)
                self.assertEqual(
                    response.status_code,
                    status.HTTP_400_BAD_REQUEST,
                )
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
