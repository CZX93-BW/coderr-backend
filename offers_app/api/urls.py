from django.urls import path

from .views import OfferDetailView, OfferViewSet


app_name = "offers"

urlpatterns = [
    path(
        "offers/",
        OfferViewSet.as_view({"get": "list", "post": "create"}),
        name="offer-list",
    ),
    path(
        "offers/<int:pk>/",
        OfferViewSet.as_view({"get": "retrieve"}),
        name="offer-detail",
    ),
    path(
        "offerdetails/<int:pk>/",
        OfferDetailView.as_view(),
        name="offerdetail-detail",
    ),
]