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


class IsOfferOwner(BasePermission):
    message = "Only the offer owner may change or delete this offer."

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.pk
