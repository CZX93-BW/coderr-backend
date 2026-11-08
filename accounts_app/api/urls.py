# Map API paths for accounts and role-specific profiles to their DRF views.

from django.urls import path

from .views import (
    BusinessProfileListView,
    CustomerProfileListView,
    LoginView,
    ProfileDetailView,
    RegistrationView,
)

app_name = "accounts"

urlpatterns = [
    path(
        "registration/",
        RegistrationView.as_view(),
        name="registration",
    ),
    path(
        "login/",
        LoginView.as_view(),
        name="login",
    ),
    path(
        "profile/<int:pk>/",
        ProfileDetailView.as_view(),
        name="profile-detail",
    ),
    path(
        "profiles/customer/",
        CustomerProfileListView.as_view(),
        name="customer-profile-list",
    ),
    path(
        "profiles/business/",
        BusinessProfileListView.as_view(),
        name="business-profile-list",
    ),
]
