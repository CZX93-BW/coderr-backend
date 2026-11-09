"""Map API paths for provider reviews to their DRF views."""

from django.urls import path

from .views import ReviewDetailView, ReviewListCreateView

app_name = "reviews"

urlpatterns = [
    path(
        "reviews/",
        ReviewListCreateView.as_view(),
        name="review-list",
    ),
    path(
        "reviews/<int:pk>/",
        ReviewDetailView.as_view(),
        name="review-detail",
    ),
]
