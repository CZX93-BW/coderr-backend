# List and create reviews and enforce authorship for detail writes.

from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import (
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from reviews_app.models import Review

from .filters import ReviewFilterBackend
from .permissions import IsCustomerUser, IsReviewAuthor
from .serializers import ReviewCreateSerializer, ReviewUpdateSerializer


class ReviewListCreateView(ListCreateAPIView):
    queryset = Review.objects.order_by("-updated_at", "-id")
    serializer_class = ReviewCreateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [ReviewFilterBackend]
    pagination_class = None
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        """Require a customer profile to publish a review."""
        permissions = super().get_permissions()
        if self.request.method == "POST":
            permissions.append(IsCustomerUser())
        return permissions

    def perform_create(self, serializer):
        """Assign authorship to the authenticated reviewer."""
        serializer.save(reviewer=self.request.user)


class ReviewDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewUpdateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsReviewAuthor]
    http_method_names = ["patch", "delete", "options"]
