import uuid
from types import SimpleNamespace

import pytest
from fastapi import Request as FastAPIRequest
from fastapi import Response
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core import security
from app.core.exceptions import AuthenticationError, BadRequestError
from app.services import auth_service


def _request(cookies: dict[str, str]) -> Request:
    cookie = "; ".join(f"{name}={value}" for name, value in cookies.items())
    headers = [(b"cookie", cookie.encode())] if cookie else []
    return Request({"type": "http", "method": "GET", "path": "/", "headers": headers, "query_string": b""})


class FakeDb:
    def __init__(self, user):
        self.user = user

    def get(self, model, key):
        return self.user


class TestSessionRefresh:
    def test_missing_access_cookie_refreshes_with_refresh_cookie(self, monkeypatch):
        user = SimpleNamespace(id=uuid.uuid4(), deleted_at=None)
        used = []

        def fake_refresh(request):
            used.append(request.cookies.get("refresh_token"))
            return {"sub": str(user.id)}

        monkeypatch.setattr(security, "_refresh_silently", fake_refresh)

        assert security.get_current_user(_request({"refresh_token": "r1"}), FakeDb(user), None) is user
        assert used == ["r1"]

    def test_no_cookies_still_requires_login(self):
        with pytest.raises(AuthenticationError):
            security.get_current_user(_request({}), FakeDb(None), None)

    def test_refreshed_cookies_reach_endpoints_that_return_their_own_response(self):
        from app.main import create_app

        app = create_app()

        @app.delete("/_test_refresh")
        def endpoint(request: FastAPIRequest):
            request.state.refreshed_session = ("new-access", "new-refresh")
            return Response(status_code=204)

        response = TestClient(app).delete("/_test_refresh")
        cookies = response.headers.get_list("set-cookie")

        assert any(cookie.startswith("access_token=new-access") for cookie in cookies)
        assert any(cookie.startswith("refresh_token=new-refresh") for cookie in cookies)


class TestPasswordReset:
    def _clients(self, monkeypatch, verify_result):
        seen = {}

        class Auth:
            def verify_otp(self, params):
                seen["otp"] = params
                return verify_result

        class Admin:
            def update_user_by_id(self, user_id, attributes):
                seen["update"] = (user_id, attributes)

            def sign_out(self, token, scope):
                seen["sign_out"] = (token, scope)

        monkeypatch.setattr(auth_service, "get_anon_client", lambda: SimpleNamespace(auth=Auth()))
        monkeypatch.setattr(
            auth_service, "get_admin_client", lambda: SimpleNamespace(auth=SimpleNamespace(admin=Admin()))
        )
        return seen

    def test_token_hash_is_verified_before_the_password_changes(self, monkeypatch):
        user_id = uuid.uuid4()
        result = SimpleNamespace(user=SimpleNamespace(id=user_id), session=SimpleNamespace(access_token="tok"))
        seen = self._clients(monkeypatch, result)

        auth_service.reset_password("hash123", "new-password-1")

        assert seen["otp"] == {"type": "recovery", "token_hash": "hash123"}
        assert seen["update"] == (str(user_id), {"password": "new-password-1"})
        assert seen["sign_out"] == ("tok", "global")

    def test_link_without_a_session_is_rejected(self, monkeypatch):
        seen = self._clients(monkeypatch, SimpleNamespace(user=None, session=None))

        with pytest.raises(BadRequestError):
            auth_service.reset_password("hash123", "new-password-1")

        assert "update" not in seen