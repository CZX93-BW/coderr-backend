"""Expose marketplace totals and the mean review rating without a login."""

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from base_info_app.services import get_base_info


class BaseInfoView(APIView):
    """Return public counts and the average provider rating."""

    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]

    def get(self, request):
        """Return public counts and the average review rating."""
        return Response(get_base_info())
