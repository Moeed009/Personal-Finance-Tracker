import logging
import uuid
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import ACCESS_COOKIE, REFRESH_COOKIE, set_auth_cookies
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.supabase import get_anon_client
from app.models.user import User


logger = logging.getLogger(__name__)

JWT_LEEWAY_SECONDS = 30

bearer_scheme = HTTPBearer(auto_error=False)


@lru_cache
def _jwks_client() -> PyJWKClient:
    settings = get_settings()
    return PyJWKClient(
        f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    )


def decode_access_token(token: str) -> dict:
    settings = get_settings()

    try:
        if settings.supabase_jwt_secret:
            return jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                leeway=JWT_LEEWAY_SECONDS,
            )

        signing_key = _jwks_client().get_signing_key_from_jwt(token).key

        return jwt.decode(
            token,
            signing_key,
            algorithms=["RS256", "ES256"],
            audience="authenticated",
            leeway=JWT_LEEWAY_SECONDS,
        )

    except jwt.ExpiredSignatureError:
        raise
    except jwt.PyJWTError as exc:
        logger.warning("JWT decode failed: %r", exc)
        raise AuthenticationError("Invalid authentication token") from exc


def extract_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is not None:
        return credentials.credentials

    return request.cookies.get(ACCESS_COOKIE)


def _refresh_silently(
    request: Request,
    response: Response,
) -> dict:
    refresh_token = request.cookies.get(REFRESH_COOKIE)

    if not refresh_token:
        raise AuthenticationError(
            "Session expired, please log in again"
        )

    try:
        session = (
            get_anon_client()
            .auth
            .refresh_session(refresh_token)
            .session
        )
    except Exception as exc:
        raise AuthenticationError(
            "Session expired, please log in again"
        ) from exc

    if session is None:
        raise AuthenticationError(
            "Session expired, please log in again"
        )

    if not session.access_token or not session.refresh_token:
        raise AuthenticationError(
            "Session expired, please log in again"
        )

    set_auth_cookies(
        response,
        session.access_token,
        session.refresh_token,
    )

    try:
        return decode_access_token(session.access_token)
    except jwt.PyJWTError as exc:
        raise AuthenticationError(
            "Invalid refreshed authentication token"
        ) from exc


def get_current_user(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> User:
    token = extract_token(request, credentials)

    if not token:
        logger.warning(
            "No token received (no Authorization header, no access cookie)"
        )
        raise AuthenticationError("Authentication required")

    try:
        claims = decode_access_token(token)

    except jwt.ExpiredSignatureError:
        logger.warning("Access token expired, attempting silent refresh")
        claims = _refresh_silently(request, response)

    except AuthenticationError:
        raise

    except jwt.PyJWTError as exc:
        raise AuthenticationError(
            "Invalid authentication token"
        ) from exc

    try:
        subject = claims.get("sub")

        if not subject:
            raise AuthenticationError(
                "Invalid authentication token"
            )

        user_id = uuid.UUID(subject)

    except (ValueError, AttributeError) as exc:
        raise AuthenticationError(
            "Invalid authentication token"
        ) from exc

    user = db.get(User, user_id)

    if user is None:
        raise AuthenticationError("User profile not found")

    if user.deleted_at is not None:
        raise AuthenticationError(
            "Account is pending deletion. Log in again to restore it"
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]