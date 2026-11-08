# Manage provider offers and edit their package tiers inline.

from django.contrib import admin

from .models import Offer, OfferDetail


class OfferDetailInline(admin.StackedInline):
    model = OfferDetail
    extra = 0


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "created_at", "updated_at")
    list_select_related = ("user",)
    search_fields = ("title", "description", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = (OfferDetailInline,)


@admin.register(OfferDetail)
class OfferDetailAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "offer",
        "offer_type",
        "price",
        "delivery_time_in_days",
        "revisions",
    )
    list_filter = ("offer_type",)
    list_select_related = ("offer",)
    search_fields = ("title", "offer__title")
