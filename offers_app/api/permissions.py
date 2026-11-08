# Restrict creation to business accounts and changes to the offer owner.

from rest_framework.permissions import BasePermission

from accounts_app.models import UserProfile


class IsBusinessUser(BasePermission):
    message = "Only business users can create offers."

    def has_permission(self, request, view):
        """Require an authenticated account with a business profile."""
        return (
            request.user.is_authenticated
            and UserProfile.objects.filter(
                user=request.user,
                type=UserProfile.AccountType.BUSINESS,
            ).exists()
        )


class IsOfferOwner(BasePermission):
    message = "Only the offer owner may change or delete this offer."

    def has_object_permission(self, request, view, obj):
        """Allow changes only when the requester owns the offer."""
        return obj.user_id == request.user.pk
