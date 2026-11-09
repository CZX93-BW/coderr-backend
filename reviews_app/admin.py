"""Inspect reviews by author, business account, rating and creation date."""

from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Inspect provider reviews by author, rating and creation date."""

    list_display = (
        "id",
        "business_user",
        "reviewer",
        "rating",
        "created_at",
    )
    list_filter = ("rating",)
    search_fields = (
        "business_user__username",
        "reviewer__username",
        "description",
    )
    list_select_related = ("business_user", "reviewer")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at", "-id")
