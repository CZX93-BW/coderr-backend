from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

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