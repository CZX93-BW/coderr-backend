from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsCustomerUser
from .serializers import ReviewCreateSerializer


class ReviewCreateView(CreateAPIView):
    serializer_class = ReviewCreateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsCustomerUser]
    http_method_names = ["post", "options"]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)