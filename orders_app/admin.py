from django.contrib import admin

from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "customer_user",
        "business_user",
        "offer_type",
        "price",
        "status",
        "created_at",
    )
    list_filter = ("status", "offer_type")
    search_fields = (
        "title",
        "customer_user__username",
        "business_user__username",
    )
    list_select_related = ("customer_user", "business_user")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at", "-id")
