"""Register users, issue login tokens and serve role-specific profile data."""

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from accounts_app.models import UserProfile

from .permissions import IsProfileOwnerOrReadOnly
from .serializers import (
    BusinessProfileListSerializer,
    CustomerProfileListSerializer,
    ProfileDetailSerializer,
    ProfileUpdateSerializer,
    RegistrationResponseSerializer,
    RegistrationSerializer,
)


class RegistrationView(generics.GenericAPIView):
    """Register a marketplace account and return its access token."""

    queryset = get_user_model().objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        """Register the account and return its token and public identity
        fields.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = RegistrationResponseSerializer(user)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    """Authenticate an active user and return a reusable access token."""

    queryset = get_user_model().objects.all()
    serializer_class = AuthTokenSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        """Authenticate the credentials and reuse or create the account
        token.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        Token.objects.get_or_create(user=user)
        response_serializer = RegistrationResponseSerializer(user)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )


class ProfileDetailView(generics.RetrieveAPIView):
    """Retrieve a profile by user ID or update the caller's profile."""

    queryset = UserProfile.objects.select_related("user")
    serializer_class = ProfileDetailSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsProfileOwnerOrReadOnly]
    lookup_field = "user_id"
    lookup_url_kwarg = "pk"

    def patch(self, request, *args, **kwargs):
        """Apply the partial update and return the complete profile
        representation.
        """
        profile = self.get_object()
        serializer = ProfileUpdateSerializer(
            profile,
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(profile).data)


class CustomerProfileListView(generics.ListAPIView):
    """List customer profiles for authenticated callers."""

    queryset = (
        UserProfile.objects.filter(type=UserProfile.AccountType.CUSTOMER)
        .select_related("user")
        .order_by("user_id")
    )
    serializer_class = CustomerProfileListSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = None


class BusinessProfileListView(generics.ListAPIView):
    """List provider profiles for authenticated callers."""

    queryset = (
        UserProfile.objects.filter(type=UserProfile.AccountType.BUSINESS)
        .select_related("user")
        .order_by("user_id")
    )
    serializer_class = BusinessProfileListSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = None
