from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    class AccountType(models.TextChoices):
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

    def __str__(self):
        return self.user.username