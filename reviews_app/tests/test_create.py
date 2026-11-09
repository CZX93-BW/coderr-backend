"""Check customer permissions, provider validation and duplicate reviews."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from accounts_app.models import UserProfile
from reviews_app.models import Review

User = get_user_model()


class ReviewCreateAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """Prepare shared reviews create fixtures including customer,
        business.
        """
        cls.customer = cls.create_user("review_api_customer", "customer")
        cls.business = cls.create_user("review_api_business", "business")

    @classmethod
    def create_user(cls, username, account_type):
        """Create a test account with its marketplace role."""
        user = User.objects.create_user(username=username)
        UserProfile.objects.create(user=user, type=account_type)
        Token.objects.create(user=user)
        return user

    def authenticate(self, user):
        """Set the API client token for subsequent requests."""
        token = Token.objects.get(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

    def payload(self):
        """Payload for the test request."""
        return {
            "business_user": self.business.pk,
            "rating": 5,
            "description": "Excellent work and clear communication.",
        }

    def test_customer_can_create_review(self):
        """Verify that customer can create review."""
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
        """Verify that business cannot create review."""
        self.authenticate(self.business)
        response = self.client.post(
            "/api/reviews/", self.payload(), format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Review.objects.exists())

    def test_anonymous_user_cannot_create_review(self):
        """Verify that anonymous user cannot create review."""
        response = self.client.post(
            "/api/reviews/", self.payload(), format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Review.objects.exists())

    def post_review(self, **overrides):
        """Post review."""
        data = self.payload()
        data.update(overrides)
        return self.client.post("/api/reviews/", data, format="json")

    def assert_rejected_without_data(self, data):
        """Check rejected without data."""
        response = self.client.post(
            "/api/reviews/", data, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_duplicate_review_preserves_existing_review(self):
        """Verify that duplicate review preserves existing review."""
        self.authenticate(self.customer)
        first = self.post_review()
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        before = list(Review.objects.values())
        response = self.post_review(rating=1, description="Changed text.")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(Review.objects.values()), before)

    def test_invalid_ratings_create_no_reviews(self):
        """Verify that invalid ratings create no reviews."""
        self.authenticate(self.customer)
        for rating in (-1, 0, 6, 1.5, "abc", "", None, True):
            with self.subTest(rating=rating):
                data = self.payload()
                data["rating"] = rating
                self.assert_rejected_without_data(data)

    def test_missing_and_empty_required_fields_create_no_reviews(self):
        """Verify that missing and empty required fields create no reviews."""
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
        """Verify that invalid business users create no reviews."""
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
        """Verify that client cannot choose another reviewer."""
        self.authenticate(self.customer)
        response = self.post_review(reviewer=self.business.pk)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get()
        self.assertEqual(review.reviewer, self.customer)
        self.assertEqual(response.data["reviewer"], self.customer.pk)

    def test_response_contains_documented_fields(self):
        """Verify that response contains documented fields."""
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
        """Verify that different customer business pairs can create reviews."""
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
        """Verify that invalid token cannot create review."""
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {'0' * 40}")
        response = self.post_review()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Review.objects.exists())
