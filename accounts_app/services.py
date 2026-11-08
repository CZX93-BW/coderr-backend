# Create the user, role profile and access token in one transaction.

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.authtoken.models import Token

from .models import UserProfile


@transaction.atomic
def create_registered_user(user_data, account_type):
    """Create the account, profile and token in a single transaction.

    Args:
        user_data: Validated account fields accepted by the user manager.
        account_type: Marketplace role stored on the new profile.

    Returns:
        The saved Django user with a profile and authentication token.
    """
    user = get_user_model().objects.create_user(**user_data)
    UserProfile.objects.create(user=user, type=account_type)
    Token.objects.create(user=user)
    return user
