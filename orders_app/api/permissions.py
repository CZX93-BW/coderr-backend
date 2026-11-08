# Allow customer bookings, provider status updates and staff deletions.

from rest_framework.permissions import BasePermission

from accounts_app.models import UserProfile


class IsCustomerUser(BasePermission):
    message = "Only customers may create orders."

    def has_permission(self, request, view):
        """Require an authenticated customer profile."""
        return (
            request.user.is_authenticated
            and UserProfile.objects.filter(
                user=request.user,
                type="customer",
            ).exists()
        )


class CanModifyOrder(BasePermission):
    message = "You do not have permission to modify this order."

    def has_object_permission(self, request, view, obj):
        """Allow provider status changes and staff deletion according to the
        HTTP method.
        """
        if request.method == "DELETE":
            return request.user.is_staff
        if request.method == "PATCH":
            return (
                obj.business_user_id == request.user.pk
                and UserProfile.objects.filter(
                    user=request.user,
                    type="business",
                ).exists()
            )
        return False
