from rest_framework.permissions import BasePermission

from accounts_app.models import UserProfile


class IsBusinessUser(BasePermission):
    message = "Only business users can create offers."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and UserProfile.objects.filter(
                user=request.user,
                type=UserProfile.AccountType.BUSINESS,
            ).exists()
        )