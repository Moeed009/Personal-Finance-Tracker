from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500
    default_message = "Internal server error"

    def __init__(self, message: str | None = None):
        self.message = message or self.default_message
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = 400
    default_message = "Bad request"


class AuthenticationError(AppError):
    status_code = 401
    default_message = "Not authenticated"


class NotFoundError(AppError):
    status_code = 404
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    default_message = "Conflict"
    
class TooManyRequestsError(AppError):
    status_code = 429
    default_message = "Too many requests"

class PayloadTooLargeError(AppError):
    status_code = 413
    default_message = "File too large"


class ExternalServiceError(AppError):
    status_code = 502
    default_message = "External service error"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message}, headers=headers)
