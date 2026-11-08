# Verify rating bounds, relationships and uniqueness of each review pair.

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from reviews_app.models import Review

User = get_user_model()


class ReviewModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Prepare shared reviews models fixtures including customer, other
        customer, business.
        """
        cls.customer = User.objects.create_user(username="review_customer")
        cls.other_customer = User.objects.create_user(
            username="review_other_customer",
        )
        cls.business = User.objects.create_user(username="review_business")
        cls.other_business = User.objects.create_user(
            username="review_other_business",
        )

    def review_data(self, **overrides):
        """Review data for the test request."""
        data = {
            "business_user": self.business,
            "reviewer": self.customer,
            "rating": 4,
            "description": "Reliable work and clear communication.",
        }
        data.update(overrides)
        return data

    def test_review_stores_participants_and_content(self):
        """Verify that review stores participants and content."""
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
        """Verify that review receives timestamps."""
        review = Review.objects.create(**self.review_data())
        review.refresh_from_db()
        self.assertIsNotNone(review.created_at)
        self.assertIsNotNone(review.updated_at)
        self.assertGreaterEqual(review.updated_at, review.created_at)

    def test_ratings_from_one_to_five_are_allowed(self):
        """Verify that ratings from one to five are allowed."""
        for rating in range(1, 6):
            with self.subTest(rating=rating):
                review = Review(**self.review_data(rating=rating))
                review.full_clean()
                self.assertEqual(review.rating, rating)

    def test_ratings_outside_allowed_range_are_rejected(self):
        """Verify that ratings outside allowed range are rejected."""
        for rating in (-1, 0, 6):
            with self.subTest(rating=rating):
                review = Review(**self.review_data(rating=rating))
                with self.assertRaises(ValidationError) as error:
                    review.full_clean()
                self.assertIn("rating", error.exception.message_dict)

    def test_same_customer_cannot_review_same_business_twice(self):
        """Verify that same customer cannot review same business twice."""
        Review.objects.create(**self.review_data())
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Review.objects.create(**self.review_data(rating=5))
        self.assertEqual(Review.objects.count(), 1)

    def test_different_customer_business_pairs_are_allowed(self):
        """Verify that different customer business pairs are allowed."""
        first = Review.objects.create(**self.review_data())
        second = Review.objects.create(
            **self.review_data(reviewer=self.other_customer),
        )
        third = Review.objects.create(
            **self.review_data(business_user=self.other_business),
        )
        self.assertEqual(Review.objects.count(), 3)
        self.assertEqual(len({first.pk, second.pk, third.pk}), 3)
