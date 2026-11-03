from django.urls import path

from .views import OfferViewSet


app_name = "offers"

urlpatterns = [
    path(
        "offers/",
        OfferViewSet.as_view({"get": "list", "post": "create"}),
        name="offer-list",
    ),
]