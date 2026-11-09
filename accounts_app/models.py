"""Extend each Django user with one marketplace profile and account role."""

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Store the role and marketplace details for one Django user."""

    class AccountType(models.TextChoices):
        """Identify a marketplace user as a customer or a provider."""

        CUSTOMER = "customer", "Customer"
        BUSINESS = "business", "Business"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    type = models.CharField(
        max_length=8,
        choices=AccountType.choices,
    )
    file = models.ImageField(
        upload_to="profiles/",
        blank=True,
        default="",
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    tel = models.CharField(
        max_length=50,
        blank=True,
        default="",
    )
    description = models.TextField(
        blank=True,
        default="",
    )
    working_hours = models.CharField(
        max_length=255,
        blank=True,
        default="",
    )
    uploaded_at = models.DateTimeField(
        null=True,
        blank=True,
        default=None,
    )

    def __str__(self):
        """Return the username used to identify this profile in Django
        admin.
        """
        return self.user.username
