"""Store provider offers and the price, delivery time and terms of each tier.
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Offer(models.Model):
    """Store a provider's listing and its descriptive information."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="offers",
    )
    title = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to="offers/",
        blank=True,
        default="",
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return the offer title for display."""
        return self.title


class OfferDetail(models.Model):
    """Store the terms of a single package tier within an offer."""

    class OfferType(models.TextChoices):
        """Identify the basic, standard and premium package tiers."""

        BASIC = "basic", "Basic"
        STANDARD = "standard", "Standard"
        PREMIUM = "premium", "Premium"

    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="details",
    )
    title = models.CharField(max_length=255)
    revisions = models.IntegerField(
        validators=[MinValueValidator(-1)],
    )
    delivery_time_in_days = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    features = models.JSONField(default=list)
    offer_type = models.CharField(
        max_length=8,
        choices=OfferType.choices,
    )

    class Meta:
        """Enforce one package per tier within each offer."""

        constraints = [
            models.UniqueConstraint(
                fields=["offer", "offer_type"],
                name="unique_offer_package_type",
            ),
        ]

    def __str__(self):
        """Identify the package by its parent offer and tier."""
        return f"{self.offer.title}: {self.offer_type}"
