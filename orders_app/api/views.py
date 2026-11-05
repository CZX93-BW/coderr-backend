from django.db.models import Q
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated

from orders_app.models import Order

from .permissions import CanModifyOrder, IsCustomerUser
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)


class OrderListCreateView(ListCreateAPIView):
    serializer_class = OrderSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = None
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        permissions = super().get_permissions()
        if self.request.method == "POST":
            permissions.append(IsCustomerUser())
        return permissions

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user),
        ).order_by("id")

    def perform_create(self, serializer):
        serializer.save(customer_user=self.request.user)


class OrderDetailView(
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView,
):
    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, CanModifyOrder]
    http_method_names = ["patch", "delete", "options"]

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)