from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.authtoken.models import Token

from .models import UserProfile


@transaction.atomic
def create_registered_user(user_data, account_type):
    user = get_user_model().objects.create_user(**user_data)
    UserProfile.objects.create(user=user, type=account_type)
    Token.objects.create(user=user)
    return user