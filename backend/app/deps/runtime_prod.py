import logging
import os
from contextlib import AsyncExitStack
from typing import Any, Optional

from dotenv import load_dotenv

try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
except ModuleNotFoundError:  # pragma: no cover - depends on optional local install
    AsyncPostgresSaver = None  # type: ignore[assignment]

load_dotenv()

logger = logging.getLogger(__name__)

_checkpointer_instance: Optional[Any] = None
_checkpointer_exit_stack: Optional[AsyncExitStack] = None


async def _close_checkpointer() -> None:
    """Close any active checkpointer context and clear cached state."""

    global _checkpointer_exit_stack, _checkpointer_instance

    if _checkpointer_exit_stack is not None:
        try:
            await _checkpointer_exit_stack.aclose()
        finally:
            _checkpointer_exit_stack = None

    _checkpointer_instance = None


def _get_postgres_connection_string() -> str:
    """Create PostgreSQL connection string for LangGraph checkpointer.

    Raises ``RuntimeError`` when configuration is missing or incomplete.
    """

    host = os.getenv("SUPABASE_DB_HOST")
    port = os.getenv("SUPABASE_DB_PORT")
    dbname = os.getenv("SUPABASE_DB_NAME")
    user = os.getenv("SUPABASE_DB_USER")
    password = os.getenv("SUPABASE_DB_PASSWORD")

    if not all([host, port, dbname, user, password]):
        raise RuntimeError("PostgreSQL connection parameters not fully configured")

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"


async def _init_postgres_checkpointer() -> Any:
    """Initialize an AsyncPostgresSaver using the official factory."""

    if AsyncPostgresSaver is None:
        raise RuntimeError(
            "langgraph-checkpoint-postgres is not installed. "
            "Install backend requirements before using the PostgreSQL checkpointer."
        )

    conn_string = _get_postgres_connection_string()
    stack = AsyncExitStack()

    try:
        checkpointer = await stack.enter_async_context(
            AsyncPostgresSaver.from_conn_string(conn_string)
        )

        try:
            await checkpointer.setup()
            logger.info("AsyncPostgresSaver.setup() completed")
        except Exception as setup_error:
            logger.warning("AsyncPostgresSaver.setup() failed: %s", setup_error)

        global _checkpointer_exit_stack
        _checkpointer_exit_stack = stack

        logger.info(
            "Successfully initialized PostgreSQL checkpointer with AsyncPostgresSaver"
        )
        return checkpointer
    except Exception:
        await stack.aclose()
        raise


async def get_checkpointer() -> Any:
    """Get the checkpointer instance, initializing it if necessary."""

    global _checkpointer_instance
    if _checkpointer_instance is None:
        _checkpointer_instance = await _init_postgres_checkpointer()
    return _checkpointer_instance



class LazyAsyncCheckpointer:
    def __getattr__(self, name):
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{name}'. "
            "Use await get_checkpointer() to get the checkpointer instance asynchronously."
        )


# Provide the lazy checkpointer for imports
CHECKPOINTER_POSTGRES = LazyAsyncCheckpointer()
