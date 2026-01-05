import os
from contextlib import asynccontextmanager

import pytest

from backend.app.deps import runtime_prod


POSTGRES_ENV_VARS = [
    "SUPABASE_DB_HOST",
    "SUPABASE_DB_PORT",
    "SUPABASE_DB_NAME",
    "SUPABASE_DB_USER",
    "SUPABASE_DB_PASSWORD",
]


async def _reset_checkpointer_state():
    await runtime_prod._close_checkpointer()


@pytest.fixture(autouse=True)
async def reset_env_and_state(monkeypatch):
    original_env = {key: os.environ.get(key) for key in POSTGRES_ENV_VARS}
    for key in POSTGRES_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    await _reset_checkpointer_state()
    yield
    for key, value in original_env.items():
        if value is None:
            monkeypatch.delenv(key, raising=False)
        else:
            monkeypatch.setenv(key, value)
    await _reset_checkpointer_state()


@pytest.mark.asyncio
async def test_postgres_setup_called(monkeypatch):
    await _reset_checkpointer_state()

    class DummySaver:
        def __init__(self):
            self.setup_called = 0

        async def setup(self):
            self.setup_called += 1

    created = []

    class DummyAsyncPostgresSaver:
        @classmethod
        @asynccontextmanager
        async def from_conn_string(cls, conn_string: str):
            saver = DummySaver()
            created.append(saver)
            yield saver

    for key in POSTGRES_ENV_VARS:
        monkeypatch.setenv(key, f"test-{key.lower()}")

    assert runtime_prod._get_postgres_connection_string() is not None

    monkeypatch.setattr(runtime_prod, "AsyncPostgresSaver", DummyAsyncPostgresSaver)

    first_instance = await runtime_prod.get_checkpointer()
    second_instance = await runtime_prod.get_checkpointer()

    assert created, "Expected dummy checkpointer to be created"
    assert first_instance is second_instance
    assert created[0].setup_called == 1


@pytest.mark.asyncio
async def test_missing_config_raises(monkeypatch):
    await _reset_checkpointer_state()

    with pytest.raises(RuntimeError):
        await runtime_prod.get_checkpointer()

    assert runtime_prod._checkpointer_instance is None
    assert runtime_prod._checkpointer_exit_stack is None


@pytest.mark.asyncio
async def test_factory_failure_propagates(monkeypatch):
    await _reset_checkpointer_state()

    calls = 0

    class FailingAsyncPostgresSaver:
        @classmethod
        @asynccontextmanager
        async def from_conn_string(cls, conn_string: str):
            nonlocal calls
            calls += 1
            raise RuntimeError("intentional failure")
            yield  # pragma: no cover

    for key in POSTGRES_ENV_VARS:
        monkeypatch.setenv(key, f"test-{key.lower()}")

    assert runtime_prod._get_postgres_connection_string() is not None

    monkeypatch.setattr(runtime_prod, "AsyncPostgresSaver", FailingAsyncPostgresSaver)

    with pytest.raises(RuntimeError):
        await runtime_prod.get_checkpointer()

    assert calls == 1
    assert runtime_prod._checkpointer_instance is None
    assert runtime_prod._checkpointer_exit_stack is None
