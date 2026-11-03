from django.db.models import Min
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from offers_app.models import Offer

from .filters import OfferFilterBackend
from .pagination import OfferPagination
from .permissions import IsBusinessUser
from .serializers import OfferCreateSerializer, OfferListSerializer


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
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "list":
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == "list":
            return OfferListSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)