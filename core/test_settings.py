"""Use a fast password hasher for local test runs."""

from .settings import *  # noqa: F401, F403

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
