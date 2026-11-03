from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from offers_app.models import Offer

from .permissions import IsBusinessUser
from .serializers import OfferCreateSerializer


class OfferViewSet(ModelViewSet):
    queryset = Offer.objects.all()
    serializer_class = OfferCreateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsBusinessUser]
    http_method_names = ["post", "options"]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)