from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "type", "uploaded_at")
    list_filter = ("type",)
    search_fields = ("user__username", "user__email")
    list_select_related = ("user",)
    readonly_fields = ("uploaded_at",)