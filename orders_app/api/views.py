from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated

from .permissions import IsCustomerUser
from .serializers import OrderCreateSerializer


class OrderCreateView(CreateAPIView):
    serializer_class = OrderCreateSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsCustomerUser]
    http_method_names = ["post", "options"]

    def perform_create(self, serializer):
        serializer.save(customer_user=self.request.user)