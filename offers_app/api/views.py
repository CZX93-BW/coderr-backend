# List public offers and enforce action-specific access to offers and tiers.

from django.db.models import Min
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from offers_app.models import Offer, OfferDetail

from .filters import OfferFilterBackend
from .pagination import OfferPagination
from .permissions import IsBusinessUser, IsOfferOwner
from .serializers import (
    OfferCreateSerializer,
    OfferDetailSerializer,
    OfferListSerializer,
    OfferRetrieveSerializer,
    OfferUpdateSerializer,
)


class OfferViewSet(ModelViewSet):
    queryset = (
        Offer.objects.select_related("user")
        .prefetch_related("details")
        .annotate(
            min_price=Min("details__price"),
            min_delivery_time=Min("details__delivery_time_in_days"),
        )
        .order_by("id")
    )
    serializer_class = OfferCreateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsBusinessUser]
    pagination_class = OfferPagination
    filter_backends = [OfferFilterBackend]
    http_method_names = [
        "get", "post", "patch", "delete", "head", "options",
    ]

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        if self.action == "retrieve":
            return [IsAuthenticated()]
        if self.action in ("partial_update", "destroy"):
            return [IsAuthenticated(), IsOfferOwner()]
        return super().get_permissions()

    def get_serializer_class(self):
        serializers_by_action = {
            "list": OfferListSerializer,
            "retrieve": OfferRetrieveSerializer,
            "partial_update": OfferUpdateSerializer,
        }
        return serializers_by_action.get(
            self.action,
            self.serializer_class,
        )

    def filter_queryset(self, queryset):
        if self.action == "list":
            return super().filter_queryset(queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OfferDetailView(RetrieveAPIView):
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
