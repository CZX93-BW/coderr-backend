"""Find profiles by account identity and inspect their role and upload date."""

from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Inspect marketplace accounts by role and profile upload date."""

    list_display = ("user", "type", "uploaded_at")
    list_filter = ("type",)
    search_fields = ("user__username", "user__email")
    list_select_related = ("user",)
    readonly_fields = ("uploaded_at",)
