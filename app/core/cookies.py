from fastapi import Response

from app.core.config import get_settings


ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
) -> None:
    settings = get_settings()

    cookie_options = {
        "httponly": True,
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "path": "/",
    }

    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        max_age=settings.access_cookie_max_age,
        **cookie_options,
    )

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        max_age=settings.refresh_cookie_max_age,
        **cookie_options,
    )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(
        key=ACCESS_COOKIE,
        path="/",
    )

    response.delete_cookie(
        key=REFRESH_COOKIE,
        path="/",
    )
