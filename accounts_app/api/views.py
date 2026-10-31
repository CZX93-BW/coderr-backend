from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import (
    RegistrationResponseSerializer,
    RegistrationSerializer,
)


class RegistrationView(generics.GenericAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegistrationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_serializer = RegistrationResponseSerializer(user)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class LoginView(generics.GenericAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = AuthTokenSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        Token.objects.get_or_create(user=user)
        response_serializer = RegistrationResponseSerializer(user)
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK,
        )