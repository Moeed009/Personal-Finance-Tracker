from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.cookies import ACCESS_COOKIE, set_auth_cookies
from app.core.database import get_db
from app.core.exceptions import register_exception_handlers
from app.routers import (
    accounts, alerts, auth, budgets, categories, goals, imports, insights, recurring, reports, transactions, users,
)
from app.services.user_service import create_purge_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_purge_scheduler()
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
            allow_methods=["*"], allow_headers=["*"],
        )
    register_exception_handlers(app)

    @app.middleware("http")
    async def apply_refreshed_session(request: Request, call_next):
        response = await call_next(request)
        refreshed = getattr(request.state, "refreshed_session", None)

       
        already_set = any(
            header.startswith(f"{ACCESS_COOKIE}=")
            for header in response.headers.getlist("set-cookie")
        )

        if refreshed and not already_set:
            set_auth_cookies(response, *refreshed)

        return response

    api = APIRouter(prefix="/api")
    for module in (auth, users, categories, accounts, transactions, imports, budgets, recurring, insights, goals,
                   reports, alerts):
        api.include_router(module.router)
    app.include_router(api)

    @app.get("/health", tags=["Health"])
    def health():
        return {"status": "ok"}

    @app.get("/health/database", tags=["Health"])
    def health_database(db: Annotated[Session, Depends(get_db)]):
        db.execute(text("SELECT 1"))
        return {"database": "ok"}

    return app


app = create_app()