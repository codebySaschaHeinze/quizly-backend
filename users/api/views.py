from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer
from .utils import set_auth_cookies


class RegisterView(APIView):
    """Register a new user and set auth cookies."""

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(serializer.data, status=status.HTTP_201_CREATED)
        set_auth_cookies(response, access_token, refresh_token)

        return response