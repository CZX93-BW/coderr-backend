"""Restrict review creation to customers and edits or deletion to the author.
"""

from rest_framework.permissions import BasePermission

from accounts_app.models import UserProfile


class IsCustomerUser(BasePermission):
    """Require an authenticated customer account."""

    message = "Only customers may create reviews."

    def has_permission(self, request, view):
        """Require an authenticated customer profile."""
        return (
            request.user.is_authenticated
            and UserProfile.objects.filter(
                user=request.user,
                type="customer",
            ).exists()
        )


class IsReviewAuthor(BasePermission):
    """Restrict changes and deletion to the review's author."""

    message = "Only the author may modify this review."

    def has_object_permission(self, request, view, obj):
        """Allow modification only by the account that wrote the review."""
        return obj.reviewer_id == request.user.pk
