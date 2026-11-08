from rest_framework.permissions import BasePermission

from accounts_app.models import UserProfile


class IsCustomerUser(BasePermission):
    message = "Only customers may create reviews."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and UserProfile.objects.filter(
                user=request.user,
                type="customer",
            ).exists()
        )


class IsReviewAuthor(BasePermission):
    message = "Only the author may modify this review."

    def has_object_permission(self, request, view, obj):
        return obj.reviewer_id == request.user.pk
