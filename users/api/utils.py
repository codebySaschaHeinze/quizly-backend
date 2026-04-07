from django.conf import settings


def set_auth_cookies(response, access_token, refresh_token):
    """Set auth cookies on the response."""
    response.set_cookie(
        key=settings.AUTH_COOKIE_ACCESS,
        value=access_token,
        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )

    response.set_cookie(
        key=settings.AUTH_COOKIE_REFRESH,
        value=refresh_token,
        httponly=settings.AUTH_COOKIE_HTTP_ONLY,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite=settings.AUTH_COOKIE_SAMESITE,
    )


def clear_auth_cookies(response):
    """Clear auth cookies from the response."""
    response.delete_cookie(settings.AUTH_COOKIE_ACCESS)
    response.delete_cookie(settings.AUTH_COOKIE_REFRESH)