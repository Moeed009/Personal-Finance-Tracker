import logging
import time
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

logger = logging.getLogger(__name__)

SLOW_QUERY_THRESHOLD_SECONDS = 0.2


def _register_slow_query_logging(engine: Engine) -> None:
    @event.listens_for(engine, "before_cursor_execute")
    def _start_timer(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_times", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def _log_slow_query(conn, cursor, statement, parameters, context, executemany):
        elapsed = time.perf_counter() - conn.info["query_start_times"].pop()
        if elapsed >= SLOW_QUERY_THRESHOLD_SECONDS:
            logger.warning(
                "Slow query %.0f ms: %s", elapsed * 1000, " ".join(statement.split())[:300]
            )


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    connect_args = {} if url.startswith("sqlite") else {"prepare_threshold": None}
    engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
    _register_slow_query_logging(engine)
    return engine


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()