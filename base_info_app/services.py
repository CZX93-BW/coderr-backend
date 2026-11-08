# Aggregate review ratings and count providers and offers for the public
# API.

from django.db.models import Avg, Count

from accounts_app.models import UserProfile
from offers_app.models import Offer
from reviews_app.models import Review


def get_base_info():
    """Aggregate marketplace counts and round the mean rating to one decimal
    place.

    Returns:
        Counts of offers, business profiles and reviews, plus the mean
        rating. An empty review table produces an average of 0.0.
    """
    reviews = Review.objects.aggregate(
        review_count=Count("pk"),
        average_rating=Avg("rating"),
    )
    return {
        "review_count": reviews["review_count"],
        "average_rating": round(reviews["average_rating"] or 0.0, 1),
        "business_profile_count": UserProfile.objects.filter(
            type="business",
        ).count(),
        "offer_count": Offer.objects.count(),
    }
