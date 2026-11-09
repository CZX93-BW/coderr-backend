"""Scope orders to participants and count provider orders by status."""

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import GenericAPIView, ListCreateAPIView
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts_app.models import UserProfile
from orders_app.models import Order

from .permissions import CanModifyOrder, IsCustomerUser
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderStatusSerializer,
)


class OrderListCreateView(ListCreateAPIView):
    """List a participant's orders or let a customer book a package."""

    serializer_class = OrderSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = None
    http_method_names = ["get", "post", "head", "options"]

    def get_permissions(self):
        """Require a customer profile when creating a booking."""
        permissions = super().get_permissions()
        if self.request.method == "POST":
            permissions.append(IsCustomerUser())
        return permissions

    def get_serializer_class(self):
        """Use package selection for creation and the order representation
        for reads.
        """
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderSerializer

    def get_queryset(self):
        """Return orders in which the requester is the customer or provider."""
        user = self.request.user
        return Order.objects.filter(
            Q(customer_user=user) | Q(business_user=user),
        ).order_by("id")

    def perform_create(self, serializer):
        """Bind the booking to the authenticated customer."""
        serializer.save(customer_user=self.request.user)


class OrderDetailView(
    UpdateModelMixin,
    DestroyModelMixin,
    GenericAPIView,
):
    """Update an order's status or delete it according to caller permissions.
    """

    queryset = Order.objects.all()
    serializer_class = OrderStatusSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, CanModifyOrder]
    http_method_names = ["patch", "delete", "options"]

    def patch(self, request, *args, **kwargs):
        """Apply a partial status update to the selected order."""
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Delete the selected order after the permission check."""
        return self.destroy(request, *args, **kwargs)


class OrderCountView(APIView):
    """Count a provider's orders currently in progress."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "head", "options"]
    order_status = Order.Status.IN_PROGRESS
    response_key = "order_count"

    def get(self, request, business_user_id):
        """Count orders with the configured status for the requested
        provider.
        """
        get_object_or_404(
            UserProfile,
            user_id=business_user_id,
            type="business",
        )
        count = Order.objects.filter(
            business_user_id=business_user_id,
            status=self.order_status,
        ).count()
        return Response({self.response_key: count})


class CompletedOrderCountView(OrderCountView):
    """Count a provider's completed orders."""

    order_status = Order.Status.COMPLETED
    response_key = "completed_order_count"
