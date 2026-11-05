from django.urls import path

from .views import ReviewCreateView


app_name = "reviews"

urlpatterns = [
    path(
        "reviews/",
        ReviewCreateView.as_view(),
        name="review-list",
    ),
]