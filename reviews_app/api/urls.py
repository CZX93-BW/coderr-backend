from django.urls import path

from .views import ReviewListCreateView


app_name = "reviews"

urlpatterns = [
    path(
        "reviews/",
        ReviewListCreateView.as_view(),
        name="review-list",
    ),
]