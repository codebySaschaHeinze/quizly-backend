from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView

from .serializers import LoginSerializer, RegisterSerializer
from .utils import (
    blacklist_refresh_token_from_cookies,
    clear_auth_cookies,
    set_auth_cookies,
)


class RegisterView(APIView):
    """Register a new user and set auth cookies."""

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                'detail': 'User created successfully!',
            },
            status=status.HTTP_201_CREATED,
        )
        
        set_auth_cookies(response, access_token, refresh_token)

        return response
    

class LoginView(APIView):
    """Log in a user and set auth cookies."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {
                'detail': 'Login successfully!',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                },
            },
            status=status.HTTP_200_OK,
        )

        set_auth_cookies(response, access_token, refresh_token)

        return response
    

class LogoutView(APIView):
    """Log out a user, blacklist the refresh token, and clear auth cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        blacklist_refresh_token_from_cookies(request)

        response = Response(
            {
                'detail': 'Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid.',
            },
            status=status.HTTP_200_OK,
        )
        clear_auth_cookies(response)
        return response