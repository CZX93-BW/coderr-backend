# Allow authenticated profile reads and reserve edits for the profile owner.

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProfileOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        """Allow reads and restrict writes to the user linked to the
        profile.
        """
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.pk
