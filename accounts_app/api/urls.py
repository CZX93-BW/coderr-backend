from django.urls import path

from .views import LoginView, ProfileDetailView, RegistrationView


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
]